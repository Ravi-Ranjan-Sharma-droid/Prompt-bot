import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# === Error Handler ===
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