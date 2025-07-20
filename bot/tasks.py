import logging
from datetime import datetime
from telegram.ext import ContextTypes

from bot.models import user_sessions
from bot.config import Config
from bot.database import feedback_db

logger = logging.getLogger(__name__)

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
        
        # Ensure database connection is maintained
        try:
            # Simple query to keep connection alive
            feedback_count = len(feedback_db.get_all_feedback())
            logger.info(f"Database connection verified. Current feedback count: {feedback_count}")
        except Exception as e:
            logger.error(f"Database connection error during periodic cleanup: {e}")
            # Try to reinitialize database
            try:
                feedback_db._initialize_db()
                logger.info("Database connection reinitialized")
            except Exception as e2:
                logger.error(f"Failed to reinitialize database: {e2}")
        
        logger.info("Periodic cleanup completed")
        
    except Exception as e:
        logger.error(f"Error in periodic cleanup: {str(e)}")