import logging
from datetime import datetime
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.models import get_user_session
from bot.prompts import build_prompt
from bot.api import ask_openrouter
from bot.config import Config

logger = logging.getLogger(__name__)

# === Message Handlers ===
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
            "Try to switch different model if you are using advanced mode and it is asking for payment, but payment gateway is not available.\n\n"
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