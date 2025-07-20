#!/usr/bin/env python
"""
Database Restore Script

This script restores the feedback database from a backup file.

Usage:
    python restore_database.py [backup_file]
    
    If no backup file is specified, the script will list available backups
    and prompt the user to select one.
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

def list_available_backups(backup_dir=DEFAULT_BACKUP_DIR):
    """List all available backup files"""
    if not os.path.exists(backup_dir):
        print(f"Backup directory not found: {backup_dir}")
        return []
    
    # List all backup files
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('feedback_backup_') and f.endswith('.db')]
    
    # Sort by date (newest first)
    backup_files.sort(reverse=True)
    
    return backup_files

def restore_database(backup_file, db_path=DEFAULT_DB_PATH):
    """Restore database from backup file"""
    try:
        # Check if backup file exists
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Check if database exists and create backup before overwriting
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pre_restore_backup = f"{db_path}.pre_restore_{timestamp}"
            shutil.copy2(db_path, pre_restore_backup)
            logger.info(f"Created pre-restore backup: {pre_restore_backup}")
        
        # Restore using SQLite's backup API
        try:
            # Connect to source (backup) database
            source_conn = sqlite3.connect(backup_file)
            
            # Connect to destination database
            dest_conn = sqlite3.connect(db_path)
            
            # Perform restore (backup in reverse direction)
            source_conn.backup(dest_conn)
            
            # Close connections
            source_conn.close()
            dest_conn.close()
            
            logger.info(f"Database restored from: {backup_file}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error during restore: {e}")
            
            # Fallback to file copy if SQLite backup fails
            logger.info("Attempting fallback to file copy method...")
            shutil.copy2(backup_file, db_path)
            
            if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
                logger.info(f"Database restored using file copy method")
                return True
            else:
                logger.error("Restore failed using both methods")
                return False
    
    except Exception as e:
        logger.error(f"Error during database restore: {e}")
        return False

def verify_restored_database(db_path=DEFAULT_DB_PATH):
    """Verify the restored database is valid and contains data"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if feedback table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
        if not cursor.fetchone():
            logger.error("Verification failed: feedback table not found")
            conn.close()
            return False
        
        # Count feedback entries
        cursor.execute("SELECT COUNT(*) FROM feedback")
        count = cursor.fetchone()[0]
        
        # Close connection
        conn.close()
        
        logger.info(f"Verification successful: database contains {count} feedback entries")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("Database Restore Script")
    print("=======================")
    
    # Get backup file from command line argument or prompt user
    if len(sys.argv) > 1:
        backup_file = sys.argv[1]
        if not os.path.exists(backup_file):
            print(f"Error: Backup file not found: {backup_file}")
            sys.exit(1)
    else:
        # List available backups
        print("\nAvailable backups:")
        backup_files = list_available_backups()
        
        if not backup_files:
            print("No backup files found.")
            sys.exit(1)
        
        # Display backups with numbers
        for i, filename in enumerate(backup_files):
            # Extract date from filename
            try:
                date_str = filename.replace('feedback_backup_', '').replace('.db', '')
                file_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                formatted_date = file_date.strftime('%Y-%m-%d %H:%M:%S')
                
                # Get file size
                file_path = os.path.join(DEFAULT_BACKUP_DIR, filename)
                file_size = os.path.getsize(file_path) / 1024  # KB
                
                print(f"{i+1}. {formatted_date} ({file_size:.1f} KB)")
            except:
                print(f"{i+1}. {filename}")
        
        # Prompt user to select a backup
        while True:
            try:
                choice = int(input("\nEnter backup number to restore (0 to cancel): "))
                if choice == 0:
                    print("Restore cancelled.")
                    sys.exit(0)
                elif 1 <= choice <= len(backup_files):
                    backup_file = os.path.join(DEFAULT_BACKUP_DIR, backup_files[choice-1])
                    break
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(backup_files)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    
    # Confirm restore
    print(f"\nSelected backup: {os.path.basename(backup_file)}")
    print(f"Database path: {DEFAULT_DB_PATH}")
    
    response = input("\nWARNING: This will overwrite the current database. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Restore cancelled.")
        sys.exit(0)
    
    # Perform restore
    print("\nRestoring database...")
    success = restore_database(backup_file, DEFAULT_DB_PATH)
    
    if success:
        print("Database restored successfully!")
        
        # Verify restored database
        print("\nVerifying restored database...")
        if verify_restored_database(DEFAULT_DB_PATH):
            print("Verification successful!")
        else:
            print("Verification failed. The database may be corrupted.")
    else:
        print("\nRestore failed. Check the log for details.")
        sys.exit(1)