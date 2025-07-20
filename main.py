import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# Import bot modules
from bot.config import Config, logger
from bot.handlers.commands import start, help_command, history_command, model_command, feedback_command, status_command
from bot.handlers.messages import handle_message
from bot.handlers.callbacks import button_handler
from bot.handlers.errors import error_handler
from bot.handlers.admin import export_feedback
from bot.handlers.stats import feedback_stats
from bot.tasks import periodic_cleanup
from bot.database import feedback_db

# === Main Application ===
def main() -> None:
    """Start the bot with enhanced configuration."""
    try:
        # Validate configuration
        Config.validate()
        
        # Initialize database connection
        logger.info("Initializing database connection...")
        # Database is already initialized through import
        
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("history", history_command))
        application.add_handler(CommandHandler("model", model_command))
        application.add_handler(CommandHandler("feedback", feedback_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("export_feedback", export_feedback))
        application.add_handler(CommandHandler("feedback_stats", feedback_stats))
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
        
        # Register shutdown handler to close database connection
        def shutdown():
            logger.info("Shutting down, closing database connection...")
            feedback_db.close()
            logger.info("Shutdown complete")
        
        # Start the bot with shutdown handler
        application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
        
        # Close database connection on shutdown
        shutdown()
        logger.info("🛑 Bot has stopped.")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise

if __name__ == "__main__":
    main()