#!/usr/bin/env python
"""
Feedback Migration Script

This script migrates existing in-memory feedback to the SQLite database.
It's useful when upgrading from a version without database support.

Usage:
    python migrate_feedback.py
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import bot modules
from bot.models import user_sessions
from bot.database import feedback_db

def migrate_feedback():
    """Migrate in-memory feedback to SQLite database"""
    try:
        total_migrated = 0
        total_users = 0
        
        logger.info("Starting feedback migration...")
        
        # Iterate through all user sessions
        for user_id, session in user_sessions.items():
            if session.feedback_history:
                total_users += 1
                user_migrated = 0
                
                # Migrate each feedback item
                for feedback_item in session.feedback_history:
                    feedback_text = feedback_item.get('feedback', '')
                    if feedback_text:
                        # Add to database
                        success = feedback_db.add_feedback(user_id, feedback_text)
                        if success:
                            total_migrated += 1
                            user_migrated += 1
                
                logger.info(f"Migrated {user_migrated} feedback items for user {user_id}")
        
        logger.info(f"Migration complete. Migrated {total_migrated} feedback items from {total_users} users.")
        return total_migrated, total_users
    
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return 0, 0

def verify_migration():
    """Verify that feedback was migrated correctly"""
    try:
        # Get all feedback from database
        all_feedback = feedback_db.get_all_feedback()
        
        # Count in-memory feedback
        memory_count = 0
        for user_id, session in user_sessions.items():
            memory_count += len(session.feedback_history)
        
        logger.info(f"Verification: {len(all_feedback)} items in database, {memory_count} items in memory")
        
        return len(all_feedback), memory_count
    
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return 0, 0

if __name__ == "__main__":
    print("Feedback Migration Script")
    print("=========================")
    
    # Check if database exists
    if not os.path.exists(feedback_db.db_path):
        print(f"Creating new database at {feedback_db.db_path}")
    else:
        print(f"Using existing database at {feedback_db.db_path}")
    
    # Confirm migration
    response = input("\nThis will migrate all in-memory feedback to the SQLite database.\nContinue? (y/n): ")
    
    if response.lower() != 'y':
        print("Migration cancelled.")
        sys.exit(0)
    
    # Perform migration
    print("\nMigrating feedback...")
    total_migrated, total_users = migrate_feedback()
    
    # Verify migration
    print("\nVerifying migration...")
    db_count, memory_count = verify_migration()
    
    # Summary
    print("\nMigration Summary:")
    print(f"- Migrated {total_migrated} feedback items from {total_users} users")
    print(f"- Database now contains {db_count} feedback items")
    print(f"- In-memory storage contains {memory_count} feedback items")
    
    print("\nMigration complete!")