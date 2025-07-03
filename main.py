import requests
import os
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# === Setup logging ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# === Configuration ===
class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENROUTER_API_KEY_01 = os.getenv("OPENROUTER_API_KEY_01")  # Free mode default
    OPENROUTER_API_KEY_02 = os.getenv("OPENROUTER_API_KEY_02")  # Advanced mode default
    
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODELS = {
        "free": "deepseek/deepseek-r1-0528-qwen3-8b:free",
        "advanced": "anthropic/claude-3-opus",
    }
    
    # API key status tracking
    api_status = {
        "key_01": True,  # Available
        "key_02": True   # Available
    }
    
    @classmethod
    def get_api_key_for_mode(cls, mode: str) -> str:
        """Get the appropriate API key for the given mode with fallback logic."""
        if mode == "free":
            # Try API key 01 first (default for free)
            if cls.api_status["key_01"] and cls.OPENROUTER_API_KEY_01:
                return cls.OPENROUTER_API_KEY_01
            # Fallback to API key 02
            elif cls.api_status["key_02"] and cls.OPENROUTER_API_KEY_02:
                logger.warning("API key 01 unavailable, using API key 02 for free mode")
                return cls.OPENROUTER_API_KEY_02
        else:  # advanced mode
            # Try API key 02 first (default for advanced)
            if cls.api_status["key_02"] and cls.OPENROUTER_API_KEY_02:
                return cls.OPENROUTER_API_KEY_02
            # Fallback to API key 01
            elif cls.api_status["key_01"] and cls.OPENROUTER_API_KEY_01:
                logger.warning("API key 02 unavailable, using API key 01 for advanced mode")
                return cls.OPENROUTER_API_KEY_01
        
        raise ValueError("No API keys available")
    
    @classmethod
    def mark_api_key_failed(cls, api_key: str):
        """Mark an API key as failed."""
        if api_key == cls.OPENROUTER_API_KEY_01:
            cls.api_status["key_01"] = False
            logger.error("API key 01 marked as failed")
        elif api_key == cls.OPENROUTER_API_KEY_02:
            cls.api_status["key_02"] = False
            logger.error("API key 02 marked as failed")
    
    @classmethod
    def reset_api_status(cls):
        """Reset API key status (call periodically to retry failed keys)."""
        cls.api_status = {"key_01": True, "key_02": True}
    
    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        if not cls.OPENROUTER_API_KEY_01 and not cls.OPENROUTER_API_KEY_02:
            raise ValueError("At least one OPENROUTER_API_KEY must be provided")
        
        # Log available API keys
        keys_available = []
        if cls.OPENROUTER_API_KEY_01:
            keys_available.append("API_KEY_01")
        if cls.OPENROUTER_API_KEY_02:
            keys_available.append("API_KEY_02")
        
        logger.info(f"Available API keys: {', '.join(keys_available)}")

Config.validate()

# === Data Models ===
class UserSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.history: List[Dict] = []
        self.preferred_model: str = Config.MODELS["free"]
        self.last_interaction: datetime = datetime.now()
        self.feedback_history: List[Dict] = []
    
    def add_to_history(self, original: str, enhanced: str, model_used: str = None):
        """Add a new entry to the user's history"""
        self.history.append({
            "original": original,
            "enhanced": enhanced,
            "model_used": model_used or "unknown",
            "timestamp": datetime.now().isoformat()
        })
        # Keep only the last 20 items
        if len(self.history) > 20:
            self.history = self.history[-20:]
        self.last_interaction = datetime.now()
    
    def add_feedback(self, feedback: str):
        """Add feedback to user's feedback history"""
        self.feedback_history.append({
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only the last 50 feedback items
        if len(self.feedback_history) > 50:
            self.feedback_history = self.feedback_history[-50:]

# Global session storage (in production, use a database)
user_sessions: Dict[int, UserSession] = {}

def get_user_session(user_id: int) -> UserSession:
    """Get or create a user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    return user_sessions[user_id]

# === Prompt Engineering ===
def build_prompt(user_input: str, context: Optional[str] = None) -> List[Dict]:
    """
    Constructs the message list for the API with enhanced context handling.
    """
    system_prompt = (
        "You are a world-class prompt engineer. Your task is to enhance raw user input into "
        "a detailed, structured prompt for an AI model. Consider the following guidelines:\n"
        "1. Identify the user's goal and required output format\n"
        "2. Specify the AI's role and constraints\n"
        "3. Add relevant context and examples if needed\n"
        "4. Structure the prompt with clear sections\n"
        "5. Ensure the enhanced prompt is actionable and specific\n"
        "6. Make the prompt professional and comprehensive\n"
        "7. Include success criteria when appropriate\n\n"
        "Return ONLY the enhanced prompt in plain text format without any additional commentary, "
        "explanations, or meta-text. Do not include phrases like 'Here's your enhanced prompt:' "
        "or any other wrapper text."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    if context:
        messages.insert(1, {"role": "assistant", "content": context})
    
    return messages

# === API Communication ===
async def ask_openrouter(messages: List[Dict], model: str, mode: str = "free") -> Tuple[str, str]:
    """
    Enhanced API communication with dual API key support and fallback logic.
    Returns: (response_text, model_used)
    """
    max_retries = 2
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Get appropriate API key
            api_key = Config.get_api_key_for_mode(mode)
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",
                "X-Title": "Advanced Prompt Enhancer Bot"
            }

            data = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }

            response = requests.post(
                Config.OPENROUTER_URL,
                headers=headers,
                json=data,
                timeout=45
            )
            
            if response.status_code == 401:
                # API key is invalid, mark it as failed
                Config.mark_api_key_failed(api_key)
                raise Exception("API key authentication failed")
            
            response.raise_for_status()
            
            result = response.json()
            if not result.get("choices"):
                raise ValueError("Unexpected API response format")
            
            # Determine which model was actually used
            model_used = result.get("model", model)
            
            return result["choices"][0]["message"]["content"], model_used
    
        except requests.exceptions.Timeout:
            logger.error(f"OpenRouter API timeout (attempt {attempt + 1})")
            last_error = "The AI service is taking too long to respond. Please try again."
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed (attempt {attempt + 1}): {str(e)}")
            last_error = f"Failed to communicate with the AI service: {str(e)}"
        except ValueError as e:
            logger.error(f"API response parsing failed (attempt {attempt + 1}): {str(e)}")
            last_error = "Received an unexpected response from the AI service."
        except Exception as e:
            logger.error(f"Unexpected error (attempt {attempt + 1}): {str(e)}")
            last_error = str(e)
            
            # If this was the last attempt, check if we can try with the other API key
            if attempt == max_retries - 1:
                # If we're using key_01 and key_02 is available, try again with key_02
                if mode == "free" and Config.api_status["key_02"] and Config.OPENROUTER_API_KEY_02:
                    Config.mark_api_key_failed(api_key)  # Mark current key as failed
                    logger.info("Retrying with API key 02 as fallback")
                    try:
                        return await ask_openrouter(messages, model, "advanced")
                    except Exception as inner_e:
                        last_error = str(inner_e)
                # If we're using key_02 and key_01 is available, try again with key_01
                elif mode == "advanced" and Config.api_status["key_01"] and Config.OPENROUTER_API_KEY_01:
                    Config.mark_api_key_failed(api_key)  # Mark current key as failed
                    logger.info("Retrying with API key 01 as fallback")
                    try:
                        return await ask_openrouter(messages, model, "free")
                    except Exception as inner_e:
                        last_error = str(inner_e)
    
    # If all retries failed, raise the last error
    raise Exception(last_error or "Failed to get response from AI service")

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced start command with interactive buttons and improved UI."""
    try:
        user = update.effective_user
        logger.info(f"Start command called by user: {user.id}")
        
        # Get or create user session and update last interaction time
        session = get_user_session(user.id)
        session.last_interaction = datetime.now()
        
        # Create keyboard with better organization
        keyboard = [
            [InlineKeyboardButton("🚀 Enhance a Prompt", callback_data='help_prompt')],
            [InlineKeyboardButton("💡 Example Prompts", callback_data='examples')],
            [InlineKeyboardButton("📜 View History", callback_data='view_history')],
            [InlineKeyboardButton("💬 Feedback", callback_data='feedback')],
            [InlineKeyboardButton("⚙️ Settings", callback_data='settings')],
            [InlineKeyboardButton("👨‍💻 Find Me", callback_data='find_me')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"👋 <b>Hey {user.first_name}!</b>\n\n"
            "I'm your <b>AI Prompt Enhancer</b> — here to help you craft professional, effective prompts for AI.\n\n"
            "✨ Just send me any idea, question, or goal, and I'll turn it into a clear, structured prompt that gets better results.\n\n"
            "<b>Try something like:</b>\n"
            "• <i>Explain quantum computing to a 5-year-old</i>\n"
            "• <i>Create a marketing plan for a new coffee shop</i>\n\n"
            "Choose an option below to get started:"
        )
        
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
            
        logger.info("Start command completed successfully")
        
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        error_msg = "Sorry, something went wrong. Please try again."
        if update.message:
            await update.message.reply_text(error_msg)
        else:
            await update.callback_query.edit_message_text(error_msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detailed help command."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    session.last_interaction = datetime.now()
    
    help_text = (
        "📚 <b>How to use this bot:</b>\n\n"
        "1. Simply send me your idea or what you want the AI to do\n\n"
        "2. I'll analyze it and create a detailed, structured prompt\n\n"
        "3. Use the enhanced prompt with any AI model for better results\n\n"
        "4. AI makes errors sometimes, so feel free to ask for revisions!\n\n"
        "5. If you do not receive any response, please try again later. try changing the mode\n\n"
        "6. If you still encounter issues, please contact support.\n\n"
        "7. Want to contribute? Contact the developer!\n\n"
        "8. If advance mode is asking for payment, but payment gateway is not available, but you can get access after free mode fails.\n\n"
        "9. <b>Thank you for using our bot!</b>\n\n"
        "<b>Available commands:</b>\n"
        "• /start - Main menu\n"
        "• /help - Show this help message\n"
        "• /history - View your recent prompts\n"
        "• /model - Switch between different AI models\n"
        "• /feedback - Send feedback or report issues\n"
        "• /status - Check bot and API status\n\n"
        "<i>💡 Tip: The more specific your initial idea, the better the enhanced prompt will be!</i>"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's prompt history."""
    try:
        user_id = update.effective_user.id
        session = get_user_session(user_id)
        session.last_interaction = datetime.now()
        
        if not session.history:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = "📜 You don't have any prompt history yet.\n\nStart by sending me a prompt to enhance!"
            
            if update.message:
                await update.message.reply_text(message_text, reply_markup=reply_markup)
            else:
                await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
            return
        
        history_text = "📜 <b>Your Prompt History:</b>\n\n"
        for i, item in enumerate(reversed(session.history), 1):
            timestamp = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %H:%M')
            model_used = item.get('model_used', 'unknown')
            
            history_text += (
                f"<b>#{i}:</b>\n"
                f"<i>📝 Original:</i> {item['original'][:100]}{'...' if len(item['original']) > 100 else ''}\n"
                f"<i>✨ Enhanced:</i> {item['enhanced'][:100]}{'...' if len(item['enhanced']) > 100 else ''}\n"
                f"<i>🤖 Model:</i> {model_used}\n"
                f"<i>🕒 Time:</i> {timestamp}\n\n"
            )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Split long messages to avoid Telegram's length limit
        if len(history_text) > 4000:
            parts = [history_text[i:i+4000] for i in range(0, len(history_text), 4000)]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # Last part
                    if update.message:
                        await update.message.reply_text(part, parse_mode='HTML', reply_markup=reply_markup)
                    else:
                        await update.callback_query.edit_message_text(part, parse_mode='HTML', reply_markup=reply_markup)
                else:
                    if update.message:
                        await update.message.reply_text(part, parse_mode='HTML')
                    else:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=part,
                            parse_mode='HTML'
                        )
        else:
            if update.message:
                await update.message.reply_text(history_text, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await update.callback_query.edit_message_text(history_text, parse_mode='HTML', reply_markup=reply_markup)
                
    except Exception as e:
        logger.error(f"Error in show_history: {str(e)}")
        error_msg = "Sorry, couldn't load your history. Please try again."
        if update.message:
            await update.message.reply_text(error_msg)
        else:
            await update.callback_query.edit_message_text(error_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced message handler with progress updates and better error handling."""
    user = update.effective_user
    user_id = user.id
    user_input = update.message.text.strip()
    
    # Check if user is in feedback mode
    if context.user_data.get('awaiting_feedback'):
        await handle_feedback_message(update, context)
        return
    
    if not user_input:
        await update.message.reply_text("⚠️ Please provide some text to enhance.")
        return
    
    session = get_user_session(user_id)
    
    # Update last interaction time
    session.last_interaction = datetime.now()
    
    # Send typing action to show the bot is working
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    try:
        # Step 1: Acknowledge receipt
        progress_msg = await update.message.reply_text(
            "🔍 Analyzing your input...",
            reply_to_message_id=update.message.message_id
        )
        
        # Step 2: Determine mode based on preferred model
        mode = "free" if session.preferred_model == Config.MODELS["free"] else "advanced"
        
        # Step 3: Generate enhanced prompt
        messages = build_prompt(user_input)
        enhanced_prompt, model_used = await ask_openrouter(messages, session.preferred_model, mode)
        
        # Step 4: Store in history
        session.add_to_history(user_input, enhanced_prompt, model_used)
        
        # Step 5: Send results with formatting and options
        await progress_msg.edit_text("✅ <b>Here's your enhanced prompt:</b>", parse_mode='HTML')
        
        # Split long messages to avoid Telegram's length limit
        if len(enhanced_prompt) > 4000:
            parts = [enhanced_prompt[i:i+4000] for i in range(0, len(enhanced_prompt), 4000)]
            for part in parts:
                await update.message.reply_text(f"```\n{part}\n```", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"```\n{enhanced_prompt}\n```", parse_mode='Markdown')
        
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔄 Improve Further", callback_data=f"improve:{user_id}"),
                InlineKeyboardButton("📜 View History", callback_data='view_history')
            ],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎯 <b>Put it this prompt in latest AI model for better and fruitful results | What would you like to do next?</b>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error processing message from user {user_id}: {str(e)}")
        error_msg = (
            "⚠️ <b>Oops! Something went wrong.</b>\n\n"
            f"<i>Error: {str(e)}</i>\n\n"
            "Please try again or use /help for assistance."
        )
        await update.message.reply_text(error_msg, parse_mode='HTML')

async def handle_feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle feedback messages from users."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    feedback_text = update.message.text.strip()
    
    # Update last interaction time
    session.last_interaction = datetime.now()
    
    if not feedback_text:
        await update.message.reply_text("⚠️ Please provide your feedback.")
        return
    
    # Store feedback
    session.add_feedback(feedback_text)
    
    # Log feedback for developer
    logger.info(f"Feedback from user {user_id}: {feedback_text}")
    
    # Clear feedback mode
    context.user_data['awaiting_feedback'] = False
    
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✅ <b>Thank you for your feedback!</b>\n\n"
        "Your feedback has been recorded and will help improve the bot.\n\n"
        "Is there anything else I can help you with?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses."""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        session = get_user_session(user_id)
        
        # Update last interaction time
        session.last_interaction = datetime.now()
        if data.startswith('improve:'):
            await query.edit_message_text(
                "🔄 <b>Improve Your Prompt</b>\n\n"
                "Please send your additional improvement instructions or feedback about the previous prompt.",
                parse_mode='HTML'
            )
            
        elif data == 'help_prompt':
            help_text = (
                "🚀 <b>How to Enhance Prompts:</b>\n\n"
                "1. Just type your idea or question\n"
                "2. I'll transform it into a professional prompt\n"
                "3. Copy and use with any AI model\n\n"
                "<b>Example:</b>\n"
                "<i>Input:</i> \"Write about dogs\"\n"
                "<i>Output:</i> \"Act as a professional content writer specializing in pet care. Write a comprehensive, engaging article about dogs that covers their history, popular breeds, care tips, and the human-dog bond. Use a warm, informative tone suitable for pet enthusiasts. Include practical advice and interesting facts. Target length: 800-1000 words.\"\n\n"
                "✨ <b>Ready to try? Send me your idea!</b>"
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='HTML')
            
        elif data == 'view_history':
            if not session.history:
                keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📜 <b>Your History is Empty</b>\n\n"
                    "You haven't enhanced any prompts yet. Start by sending me an idea!",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return
            
            history_text = "📜 <b>Your Recent Prompts:</b>\n\n"
            for i, item in enumerate(reversed(session.history[-5:]), 1):  # Show last 5
                timestamp = datetime.fromisoformat(item['timestamp']).strftime('%m/%d %H:%M')
                history_text += (
                    f"<b>#{i}.</b> {item['original'][:80]}{'...' if len(item['original']) > 80 else ''}\n"
                    f"<i>🕒 {timestamp}</i>\n\n"
                )
            
            keyboard = [
                [InlineKeyboardButton("📋 View Full History", callback_data='full_history')],
                [InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                history_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif data == 'full_history':
            await show_history(update, context)
            
        elif data == 'examples':
            examples = (
                "💡 <b>Example Inputs & Outputs:</b>\n\n"
                "<b>1. Simple Input:</b>\n"
                "<i>\"Explain blockchain\"</i>\n"
                "<b>Enhanced:</b> Professional explanation with analogies, examples, and structured format\n\n"
                "<b>2. Creative Input:</b>\n"
                "<i>\"Write a story about space\"</i>\n"
                "<b>Enhanced:</b> Detailed creative brief with genre, characters, setting, and style guidelines\n\n"
                "<b>3. Technical Input:</b>\n"
                "<i>\"Python code for data analysis\"</i>\n"
                "<b>Enhanced:</b> Specific requirements, libraries, documentation, and best practices\n\n"
                "<b>4. Business Input:</b>\n"
                "<i>\"Marketing strategy for restaurant\"</i>\n"
                "<b>Enhanced:</b> Comprehensive brief with target audience, channels, budget, and metrics\n\n"
                "✨ <b>Ready to try? Send me your idea!</b>"
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(examples, reply_markup=reply_markup, parse_mode='HTML')
            
        elif data == 'settings':
            current_model = "Free Model" if session.preferred_model == Config.MODELS["free"] else "Advanced Model"
            settings_text = (
                "⚙️ <b>Settings</b>\n\n"
                f"<b>Current Model:</b> {current_model}\n"
                f"<b>Prompts in History:</b> {len(session.history)}\n"
                f"<b>Feedback Items:</b> {len(session.feedback_history)}\n"
                f"<b>Last Active:</b> {session.last_interaction.strftime('%Y-%m-%d %H:%M')}\n\n"
                "Configure your preferences below:"
            )
            
            keyboard = [
                [InlineKeyboardButton("🤖 Change Model", callback_data='change_model')],
                [InlineKeyboardButton("🗑 Clear History", callback_data='clear_history')],
                [InlineKeyboardButton("📊 Bot Status", callback_data='bot_status')],
                [InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                settings_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif data == 'change_model':
            current_model = "Free" if session.preferred_model == Config.MODELS["free"] else "Advanced"
            keyboard = [
                [
                    InlineKeyboardButton("🆓 Free Model", callback_data='set_model:free'),
                    InlineKeyboardButton("⭐ Advanced Model", callback_data='set_model:advanced')
                ],
                [InlineKeyboardButton("🔙 Back to Settings", callback_data='settings')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            model_text = (
                "🤖 <b>Choose Your Model:</b>\n\n"
                f"<b>Current:</b> {current_model} Model\n\n"
                "<b>🆓 Free Model:</b>\n"
                "• Fast response times\n"
                "• Good for basic prompt enhancement\n"
                "• No usage limits\n"
                "• Uses API Key 01 by default\n\n"
                "<b>⭐ Advanced Model:</b>\n"
                "• Superior quality outputs\n"
                "• Better understanding of complex requests\n"
                "• More creative and detailed enhancements\n"
                "• Uses API Key 02 by default"
            )
            
            await query.edit_message_text(
                model_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif data.startswith('set_model:'):
            model_type = data.split(':')[1]
            session.preferred_model = Config.MODELS[model_type]
            model_name = "Free" if model_type == "free" else "Advanced"
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Settings", callback_data='settings')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ <b>Model Updated!</b>\n\n"
                f"Now using: <b>{model_name} Model</b>\n\n"
                "Your next prompts will use this model.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif data == 'clear_history':
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, Clear All", callback_data='confirm_clear'),
                    InlineKeyboardButton("❌ Cancel", callback_data='settings')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🗑 <b>Clear History?</b>\n\n"
                f"This will permanently delete all {len(session.history)} prompts from your history.\n\n"
                "Are you sure you want to continue?",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif data == 'confirm_clear':
            session.history = []
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ <b>History Cleared!</b>\n\n"
                "Your prompt history has been successfully deleted.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif data == 'bot_status':
            # Check API key status
            api1_status = "✅ Online" if Config.api_status["key_01"] else "❌ Offline"
            api2_status = "✅ Online" if Config.api_status["key_02"] else "❌ Offline"
            
            status_text = (
                "📊 <b>Bot Status</b>\n\n"
                f"<b>API Key 01 (Free):</b> {api1_status}\n"
                f"<b>API Key 02 (Advanced):</b> {api2_status}\n\n"
                f"<b>Total Users:</b> {len(user_sessions)}\n"
                f"<b>Total Prompts Generated:</b> {sum(len(session.history) for session in user_sessions.values())}\n"
                f"<b>Bot Uptime:</b> Since last restart\n\n"
                "<i>Note: If an API key is offline, the bot will automatically use the working key for both modes.</i>"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 Reset API Status", callback_data='reset_api')],
                [InlineKeyboardButton("🔙 Back to Settings", callback_data='settings')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                status_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif data == 'reset_api':
            Config.reset_api_status()
            keyboard = [[InlineKeyboardButton("🔙 Back to Status", callback_data='bot_status')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ <b>API Status Reset!</b>\n\n"
                "All API keys have been marked as available again.\n"
                "The bot will retry using both keys.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif data == 'feedback':
            await query.edit_message_text(
                "💬 <b>Send Your Feedback</b>\n\n"
                "Please type your feedback, suggestions, or report any issues you've encountered.\n\n"
                "Your feedback helps improve the bot for everyone! 🚀",
                parse_mode='HTML'
            )
            # Set user in feedback mode
            context.user_data['awaiting_feedback'] = True
            
        elif data == 'find_me':
            keyboard = [
                [InlineKeyboardButton("📱 Open Instagram", url='https://www.instagram.com/nr_snorlax/')],
                [InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            find_me_text = (
                "👨‍💻 <b>Find Me Online!</b>\n\n"
                "Hi! I'm the developer behind this bot.\n\n"
                "📱 <b>Follow me on Instagram: nr_snorlax</b>\n\n"
                "🚀 <b>What you'll find:</b>\n\n"
                "• Behind-the-scenes development\n"
                "• AI and tech updates\n"
                "• Cool projects and tutorials on my <b>GitHub</b>\n"
                "• Direct contact for suggestions\n\n"
                "Click the button below to visit my profile!"
            )
            
            await query.edit_message_text(
                find_me_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif data == 'back_to_main':
            await start(update, context)
            
    except Exception as e:
        logger.error(f"Error in button_handler: {str(e)}")
        await query.edit_message_text(
            "😞 <b>Something went wrong</b>\n\n"
            "Please try again or use /help for assistance.",
            parse_mode='HTML'
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if update and hasattr(update, 'effective_chat') and update.effective_chat:
        try:
            error_msg = (
                "😞 <b>Something went wrong</b>\n\n"
                "The error has been logged and will be fixed soon.\n\n"
                "Please try again or use /help for assistance."
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_msg,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {str(e)}")

# === Command Handlers ===
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /history command."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    session.last_interaction = datetime.now()
    await show_history(update, context)

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /model command."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    session.last_interaction = datetime.now()
    current_model = "Free" if session.preferred_model == Config.MODELS["free"] else "Advanced"
    
    keyboard = [
        [
            InlineKeyboardButton("🆓 Free Model", callback_data='set_model:free'),
            InlineKeyboardButton("⭐ Advanced Model", callback_data='set_model:advanced')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🤖 <b>Current Model:</b> {current_model}\n\n"
        "Choose a different model:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /feedback command."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    session.last_interaction = datetime.now()
    await update.message.reply_text(
        "💬 <b>Send Your Feedback</b>\n\n"
        "Please type your feedback, suggestions, or report any issues you've encountered.\n\n"
        "Your feedback helps improve the bot for everyone! 🚀",
        parse_mode='HTML'
    )
    # Set user in feedback mode
    context.user_data['awaiting_feedback'] = True

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /status command."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    session.last_interaction = datetime.now()
    
    # Check API key status
    api1_status = "✅ Online" if Config.api_status["key_01"] else "❌ Offline"
    api2_status = "✅ Online" if Config.api_status["key_02"] else "❌ Offline"
    
    status_text = (
        "📊 <b>Bot Status</b>\n\n"
        f"<b>API Key 01 (Free):</b> {api1_status}\n"
        f"<b>API Key 02 (Advanced):</b> {api2_status}\n\n"
        f"<b>Total Users:</b> {len(user_sessions)}\n"
        f"<b>Total Prompts Generated:</b> {sum(len(session.history) for session in user_sessions.values())}\n"
        f"<b>Bot Uptime:</b> Since last restart\n\n"
        "<i>Note: If an API key is offline, the bot will automatically use the working key for both modes.</i>"
    )
    
    await update.message.reply_text(status_text, parse_mode='HTML')

# === Periodic Tasks ===
async def periodic_cleanup(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periodic cleanup task to remove old sessions and reset API status."""
    try:
        current_time = datetime.now()
        
        # Remove sessions inactive for more than 7 days
        inactive_users = []
        for user_id, session in user_sessions.items():
            if (current_time - session.last_interaction).days > 7:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            del user_sessions[user_id]
            logger.info(f"Removed inactive user session: {user_id}")
        
        # Reset API status every hour (in case of temporary issues)
        Config.reset_api_status()
        logger.info("Periodic cleanup completed")
        
    except Exception as e:
        logger.error(f"Error in periodic cleanup: {str(e)}")

# === Main Application ===
def main() -> None:
    """Start the bot with enhanced configuration."""
    try:
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("history", history_command))
        application.add_handler(CommandHandler("model", model_command))
        application.add_handler(CommandHandler("feedback", feedback_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        # Add periodic cleanup job (runs every hour)
        job_queue = application.job_queue
        job_queue.run_repeating(periodic_cleanup, interval=3600, first=3600)
        
        # Start the bot
        logger.info("🚀 Bot is starting...")
        logger.info(f"Available API keys: {', '.join(['API_KEY_01' if Config.OPENROUTER_API_KEY_01 else '', 'API_KEY_02' if Config.OPENROUTER_API_KEY_02 else '']).strip(', ')}")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("🛑 Bot has stopped.")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise

if __name__ == "__main__":
    main()