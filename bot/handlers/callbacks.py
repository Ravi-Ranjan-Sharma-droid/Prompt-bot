import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.models import get_user_session
from bot.config import Config
from bot.handlers.messages import show_history
from bot.handlers.commands import start

logger = logging.getLogger(__name__)

# === Button Handlers ===
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
                "• Uses Deepseek by default\n\n"
                "<b>⭐ Advanced Model:</b>\n"
                "• Superior quality outputs\n"
                "• Better understanding of complex requests\n"
                "• More creative and detailed enhancements\n"
                "• Uses Claude by default"
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
                f"<b>Deepseek (Free):</b> {api1_status}\n"
                f"<b>claude (Advanced):</b> {api2_status}\n\n"
                f"<b>Total Users:</b> {len(get_user_session.__globals__['user_sessions'])}\n"
                f"<b>Total Prompts Generated:</b> {sum(len(session.history) for session in get_user_session.__globals__['user_sessions'].values())}\n"
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