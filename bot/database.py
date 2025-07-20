import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import os

logger = logging.getLogger(__name__)

class FeedbackDatabase:
    """Class to handle all database operations for feedback storage"""
    
    def __init__(self, db_path: str = "feedback.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Create the database and tables if they don't exist"""
        try:
            # Create database directory if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                
            # Connect to database
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create feedback table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                feedback_text TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            ''')
            
            # Add index on username for better query performance
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_username ON feedback(username)')
            
            # Add index on user_id for better query performance
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)')
            
            self.conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except sqlite3.OperationalError as e:
            logger.error(f"SQLite operational error initializing database: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_feedback(self, user_id: int, feedback_text: str, username: Optional[str] = None) -> bool:
        """Add a new feedback entry to the database
        
        Args:
            user_id: The Telegram user ID
            feedback_text: The feedback text content
            username: Optional username or display name
            
        Returns:
            True if feedback was successfully added, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from bot.utils.username import sanitize_username
            
            # Sanitize the username
            sanitized_username = sanitize_username(username)
            
            timestamp = datetime.now().isoformat()
            self.cursor.execute(
                "INSERT INTO feedback (user_id, username, feedback_text, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, sanitized_username, feedback_text, timestamp)
            )
            self.conn.commit()
            logger.info(f"Feedback from user {user_id} ({sanitized_username or 'unknown'}) stored in database")
            return True
        except sqlite3.Error as e:
            logger.error(f"SQLite error adding feedback to database: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding feedback to database: {e}")
            return False
    
    def get_all_feedback(self) -> List[Dict]:
        """Retrieve all feedback entries from the database"""
        try:
            self.cursor.execute("SELECT id, user_id, username, feedback_text, timestamp FROM feedback ORDER BY timestamp DESC")
            rows = self.cursor.fetchall()
            
            feedback_list = []
            for row in rows:
                feedback_list.append({
                    "id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "feedback_text": row[3],
                    "timestamp": row[4]
                })
            
            return feedback_list
        except Exception as e:
            logger.error(f"Error retrieving feedback from database: {e}")
            return []
    
    def get_user_feedback(self, user_id: int) -> List[Dict]:
        """Retrieve all feedback entries for a specific user"""
        try:
            self.cursor.execute(
                "SELECT id, user_id, username, feedback_text, timestamp FROM feedback WHERE user_id = ? ORDER BY timestamp DESC",
                (user_id,)
            )
            rows = self.cursor.fetchall()
            
            feedback_list = []
            for row in rows:
                feedback_list.append({
                    "id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "feedback_text": row[3],
                    "timestamp": row[4]
                })
            
            return feedback_list
        except Exception as e:
            logger.error(f"Error retrieving user feedback from database: {e}")
            return []
    
    def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

# Create a singleton instance
feedback_db = FeedbackDatabase()