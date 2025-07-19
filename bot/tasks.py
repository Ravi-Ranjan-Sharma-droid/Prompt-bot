import logging
from datetime import datetime
from telegram.ext import ContextTypes

from bot.models import user_sessions
from bot.config import Config

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
        logger.info("Periodic cleanup completed")
        
    except Exception as e:
        logger.error(f"Error in periodic cleanup: {str(e)}")