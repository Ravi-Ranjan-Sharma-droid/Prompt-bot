#!/usr/bin/env python
"""
Database Backup Script

This script creates a backup of the feedback database.
It can be scheduled to run regularly using cron or Windows Task Scheduler.

Usage:
    python backup_database.py [backup_dir]
"""

import sys
import os
import shutil
import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'feedback.db')
DEFAULT_BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')

def backup_database(db_path=DEFAULT_DB_PATH, backup_dir=DEFAULT_BACKUP_DIR):
    """Create a backup of the SQLite database"""
    try:
        # Check if database exists
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return False
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            logger.info(f"Created backup directory: {backup_dir}")
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"feedback_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create backup using SQLite's backup API (more reliable than file copy)
        try:
            # Connect to source database
            source_conn = sqlite3.connect(db_path)
            
            # Connect to destination database (will be created)
            dest_conn = sqlite3.connect(backup_path)
            
            # Perform backup
            source_conn.backup(dest_conn)
            
            # Close connections
            source_conn.close()
            dest_conn.close()
            
            logger.info(f"Database backup created: {backup_path}")
            
            # Verify backup file exists and has size
            if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                logger.info(f"Backup verified: {os.path.getsize(backup_path)} bytes")
                return True
            else:
                logger.error("Backup verification failed: file missing or empty")
                return False
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error during backup: {e}")
            
            # Fallback to file copy if SQLite backup fails
            logger.info("Attempting fallback to file copy method...")
            shutil.copy2(db_path, backup_path)
            
            if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                logger.info(f"Backup created using file copy: {backup_path}")
                return True
            else:
                logger.error("Backup failed using both methods")
                return False
    
    except Exception as e:
        logger.error(f"Error during database backup: {e}")
        return False

def cleanup_old_backups(backup_dir=DEFAULT_BACKUP_DIR, keep_days=30):
    """Remove backup files older than specified days"""
    try:
        if not os.path.exists(backup_dir):
            return
        
        # Get current time
        now = datetime.now()
        
        # List all backup files
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('feedback_backup_') and f.endswith('.db')]
        
        removed_count = 0
        for filename in backup_files:
            try:
                # Extract date from filename (format: feedback_backup_YYYYMMDD_HHMMSS.db)
                date_str = filename.replace('feedback_backup_', '').replace('.db', '')
                file_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                
                # Calculate age in days
                age_days = (now - file_date).days
                
                # Remove if older than keep_days
                if age_days > keep_days:
                    file_path = os.path.join(backup_dir, filename)
                    os.remove(file_path)
                    removed_count += 1
                    logger.info(f"Removed old backup: {filename} (age: {age_days} days)")
            
            except (ValueError, OSError) as e:
                logger.warning(f"Error processing backup file {filename}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleanup complete: removed {removed_count} old backup(s)")
        
    except Exception as e:
        logger.error(f"Error during backup cleanup: {e}")

if __name__ == "__main__":
    print("Database Backup Script")
    print("======================")
    
    # Get backup directory from command line argument or use default
    backup_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BACKUP_DIR
    
    print(f"Database path: {DEFAULT_DB_PATH}")
    print(f"Backup directory: {backup_dir}")
    
    # Perform backup
    print("\nCreating backup...")
    success = backup_database(DEFAULT_DB_PATH, backup_dir)
    
    if success:
        print("Backup created successfully!")
        
        # Clean up old backups
        print("\nCleaning up old backups...")
        cleanup_old_backups(backup_dir)
        
        print("\nBackup process complete!")
    else:
        print("\nBackup failed. Check the log for details.")
        sys.exit(1)