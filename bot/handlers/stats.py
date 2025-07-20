import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
from telegram import Update
from telegram.ext import ContextTypes

from bot.database import feedback_db
from bot.config import Config
from bot.utils.username import sanitize_username

logger = logging.getLogger(__name__)

# === Statistics Command Handlers ===
async def feedback_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show feedback statistics (admin only)"""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if not hasattr(Config, 'ADMIN_IDS') or user_id not in Config.ADMIN_IDS:
        await update.message.reply_text("⚠️ You don't have permission to use this command.")
        logger.warning(f"Unauthorized access attempt to admin command by user {user_id}")
        return
    
    try:
        # Get all feedback from database
        all_feedback = feedback_db.get_all_feedback()
        
        if not all_feedback:
            await update.message.reply_text("No feedback data available.")
            return
        
        # Calculate statistics
        total_count = len(all_feedback)
        
        # Count feedback in the last 7 days
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        recent_count = 0
        
        # Count unique users and collect statistics
        unique_users: Set[int] = set()
        users_with_username = 0
        valid_usernames: Set[str] = set()
        
        for item in all_feedback:
            unique_users.add(item['user_id'])
            
            # Check if feedback has a valid username
            username = sanitize_username(item.get('username'))
            if username:
                users_with_username += 1
                valid_usernames.add(username)
            
            # Check if feedback is from the last 7 days
            try:
                feedback_time = datetime.fromisoformat(item['timestamp'])
                if feedback_time > week_ago:
                    recent_count += 1
            except (ValueError, TypeError):
                # Skip items with invalid timestamp
                logger.warning(f"Invalid timestamp format in feedback ID {item.get('id', 'unknown')}")
                pass
        
        # Prepare statistics message
        username_percentage = (users_with_username/total_count*100) if total_count > 0 else 0
        unique_username_percentage = (len(valid_usernames)/len(unique_users)*100) if len(unique_users) > 0 else 0
        
        stats_message = (
            "📊 <b>Feedback Statistics</b>\n\n"
            f"<b>Total Feedback:</b> {total_count}\n"
            f"<b>Feedback in Last 7 Days:</b> {recent_count} ({(recent_count/total_count*100):.1f}% of total)\n"
            f"<b>Unique Users:</b> {len(unique_users)}\n"
            f"<b>Feedback with Username:</b> {users_with_username} ({username_percentage:.1f}% of total)\n"
            f"<b>Unique Usernames:</b> {len(valid_usernames)} ({unique_username_percentage:.1f}% of unique users)\n\n"
            f"Use /export_feedback to download all feedback data."
        )
        
        await update.message.reply_text(stats_message, parse_mode='HTML')
        logger.info(f"Feedback statistics viewed by admin {user_id}")
        
    except Exception as e:
        logger.error(f"Error generating feedback statistics: {e}")
        await update.message.reply_text(f"⚠️ Error generating statistics: {str(e)}")