#!/usr/bin/env python
"""
Database Migration Script for Username Field

This script updates the feedback database schema to include a username field
and migrates existing data to the new schema.

Usage:
    python migrate_username.py
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# Add the parent directory to the path so we can import the bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'feedback.db')

def check_if_migration_needed(db_path=DEFAULT_DB_PATH):
    """Check if the database needs migration"""
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if username column exists
        cursor.execute("PRAGMA table_info(feedback)")
        columns = cursor.fetchall()
        
        # Close connection
        conn.close()
        
        # Check if username column exists
        for column in columns:
            if column[1] == 'username':
                logger.info("Username column already exists. No migration needed.")
                return False
        
        logger.info("Username column does not exist. Migration needed.")
        return True
        
    except Exception as e:
        logger.error(f"Error checking if migration is needed: {e}")
        return False

def migrate_database(db_path=DEFAULT_DB_PATH):
    """Migrate the database to include username column"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create backup before migration
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{db_path}.pre_migration_{timestamp}"
        
        # Backup the database
        with open(db_path, 'rb') as source:
            with open(backup_path, 'wb') as dest:
                dest.write(source.read())
        
        logger.info(f"Created backup at: {backup_path}")
        
        # Add username column to feedback table
        cursor.execute("ALTER TABLE feedback ADD COLUMN username TEXT")
        
        # Commit changes
        conn.commit()
        
        # Close connection
        conn.close()
        
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False

def verify_migration(db_path=DEFAULT_DB_PATH):
    """Verify that the migration was successful"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if username column exists
        cursor.execute("PRAGMA table_info(feedback)")
        columns = cursor.fetchall()
        
        # Close connection
        conn.close()
        
        # Check if username column exists
        for column in columns:
            if column[1] == 'username':
                logger.info("Verification successful: username column exists")
                return True
        
        logger.error("Verification failed: username column does not exist")
        return False
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False

if __name__ == "__main__":
    print("Database Migration Script for Username Field")
    print("===========================================")
    
    print(f"\nDatabase path: {DEFAULT_DB_PATH}")
    
    # Check if migration is needed
    if not check_if_migration_needed(DEFAULT_DB_PATH):
        print("\nNo migration needed. Exiting.")
        sys.exit(0)
    
    # Confirm migration
    response = input("\nThis will modify the database schema. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        sys.exit(0)
    
    # Perform migration
    print("\nMigrating database...")
    success = migrate_database(DEFAULT_DB_PATH)
    
    if success:
        print("Migration completed successfully!")
        
        # Verify migration
        print("\nVerifying migration...")
        if verify_migration(DEFAULT_DB_PATH):
            print("Verification successful!")
            print("\nThe database has been updated to include the username field.")
            print("Existing feedback entries will have NULL in the username field.")
            print("New feedback entries will include the username.")
        else:
            print("Verification failed. The migration may not have been successful.")
            print("A backup of your original database was created before migration.")
    else:
        print("\nMigration failed. Check the log for details.")
        sys.exit(1)