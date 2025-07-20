import logging
import csv
import io
from datetime import datetime
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from bot.database import feedback_db
from bot.config import Config
from bot.utils.username import sanitize_username

logger = logging.getLogger(__name__)

# === Admin Command Handlers ===
async def export_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export all feedback to a CSV file (admin only)"""
    user_id = update.effective_user.id
    
    # Check if user is an admin (you can define admin IDs in Config)
    if not hasattr(Config, 'ADMIN_IDS') or user_id not in Config.ADMIN_IDS:
        await update.message.reply_text("⚠️ You don't have permission to use this command.")
        logger.warning(f"Unauthorized access attempt to admin command by user {user_id}")
        return
    
    try:
        # Get all feedback from database
        all_feedback = feedback_db.get_all_feedback()
        
        if not all_feedback:
            await update.message.reply_text("No feedback data available to export.")
            return
        
        # Create CSV in memory
        output = io.StringIO()
        csv_writer = csv.writer(output)
        
        # Write header
        csv_writer.writerow(['ID', 'User ID', 'Username', 'Feedback', 'Timestamp'])
        
        # Write data
        for item in all_feedback:
            # Sanitize username before writing to CSV
            username = sanitize_username(item['username']) or 'Unknown'
            
            csv_writer.writerow([
                item['id'],
                item['user_id'],
                username,
                item['feedback_text'],
                item['timestamp']
            ])
        
        # Prepare file
        output.seek(0)
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f"feedback_export_{current_date}.csv"
        
        # Send file
        await update.message.reply_document(
            document=io.BytesIO(output.getvalue().encode('utf-8')),
            filename=filename,
            caption=f"📊 Feedback Export ({len(all_feedback)} entries)"
        )
        
        logger.info(f"Feedback data exported by admin {user_id}")
        
    except Exception as e:
        logger.error(f"Error exporting feedback: {e}")
        await update.message.reply_text(f"⚠️ Error exporting feedback: {str(e)}")