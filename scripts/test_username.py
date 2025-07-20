#!/usr/bin/env python
"""
Test script for username field in feedback database

This script tests the username field functionality in the feedback database
by adding test feedback entries with usernames and verifying they are stored correctly.

Usage:
    python test_username.py
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# Add the parent directory to the path so we can import the bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the database module
from bot.database import FeedbackDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_add_feedback_with_username():
    """Test adding feedback with username"""
    # Create a temporary database for testing
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_feedback.db')
    
    # Remove the test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Create a new database instance
    db = FeedbackDatabase(test_db_path)
    
    # Test data
    test_data = [
        {'user_id': 123456, 'username': 'test_user1', 'feedback': 'This is test feedback 1'},
        {'user_id': 789012, 'username': 'test_user2', 'feedback': 'This is test feedback 2'},
        {'user_id': 345678, 'username': None, 'feedback': 'This is test feedback with no username'}
    ]
    
    # Add test feedback
    for item in test_data:
        db.add_feedback(item['user_id'], item['feedback'], item['username'])
    
    # Verify the feedback was added correctly
    all_feedback = db.get_all_feedback()
    
    # Check if we have the correct number of entries
    assert len(all_feedback) == len(test_data), f"Expected {len(test_data)} entries, got {len(all_feedback)}"
    
    # Check if usernames were stored correctly
    for i, item in enumerate(test_data):
        feedback_entry = all_feedback[i]
        assert feedback_entry['user_id'] == item['user_id'], f"User ID mismatch: {feedback_entry['user_id']} != {item['user_id']}"
        assert feedback_entry['feedback_text'] == item['feedback'], f"Feedback text mismatch: {feedback_entry['feedback_text']} != {item['feedback']}"
        assert feedback_entry['username'] == item['username'], f"Username mismatch: {feedback_entry['username']} != {item['username']}"
    
    # Close the database
    db.close()
    
    # Clean up
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    logger.info("All tests passed!")
    return True

def test_get_user_feedback_with_username():
    """Test retrieving user feedback with username"""
    # Create a temporary database for testing
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_feedback.db')
    
    # Remove the test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Create a new database instance
    db = FeedbackDatabase(test_db_path)
    
    # Test user
    user_id = 123456
    username = 'test_user'
    
    # Add multiple feedback entries for the same user
    db.add_feedback(user_id, 'Feedback 1', username)
    db.add_feedback(user_id, 'Feedback 2', username)
    db.add_feedback(user_id, 'Feedback 3', username)
    
    # Add feedback for a different user
    db.add_feedback(789012, 'Different user feedback', 'other_user')
    
    # Get feedback for the test user
    user_feedback = db.get_user_feedback(user_id)
    
    # Check if we have the correct number of entries
    assert len(user_feedback) == 3, f"Expected 3 entries, got {len(user_feedback)}"
    
    # Check if usernames were stored correctly
    for feedback in user_feedback:
        assert feedback['user_id'] == user_id, f"User ID mismatch: {feedback['user_id']} != {user_id}"
        assert feedback['username'] == username, f"Username mismatch: {feedback['username']} != {username}"
    
    # Close the database
    db.close()
    
    # Clean up
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    logger.info("User feedback test passed!")
    return True

if __name__ == "__main__":
    print("Testing username field in feedback database")
    print("=========================================")
    
    try:
        # Run tests
        test_add_feedback_with_username()
        test_get_user_feedback_with_username()
        
        print("\nAll tests passed! The username field is working correctly.")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during testing: {e}")
        sys.exit(1)