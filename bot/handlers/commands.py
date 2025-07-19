import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.models import get_user_session
from bot.config import Config
from bot.handlers.messages import show_history

logger = logging.getLogger(__name__)

# === Command Handlers ===
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
        f"<b>Deepseek (Free):</b> {api1_status}\n"
        f"<b>Claude (Advanced):</b> {api2_status}\n\n"
        f"<b>Total Users:</b> {len(get_user_session.__globals__['user_sessions'])}\n"
        f"<b>Total Prompts Generated:</b> {sum(len(session.history) for session in get_user_session.__globals__['user_sessions'].values())}\n"
        f"<b>Bot Uptime:</b> Since last restart\n\n"
        "<i>Note: If an API key is offline, the bot will automatically use the working key for both modes.</i>"
    )
    
    await update.message.reply_text(status_text, parse_mode='HTML')