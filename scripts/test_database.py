#!/usr/bin/env python
"""
Database Test Script

This script tests the feedback database implementation to ensure it's working correctly.

Usage:
    python test_database.py
"""

import sys
import os
import logging
import random
import string
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
from bot.database import feedback_db

def generate_random_feedback(length=50):
    """Generate random feedback text for testing"""
    return ''.join(random.choice(string.ascii_letters + ' ') for _ in range(length))

def test_database_operations():
    """Test basic database operations"""
    print("\nTesting database operations...")
    
    # Test database initialization
    print("1. Testing database initialization...")
    try:
        feedback_db._initialize_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    
    # Test adding feedback
    print("\n2. Testing adding feedback...")
    test_user_id = 123456789
    test_feedback = f"Test feedback at {datetime.now().isoformat()}"
    
    try:
        success = feedback_db.add_feedback(test_user_id, test_feedback)
        if success:
            print(f"✓ Added feedback successfully")
        else:
            print(f"✗ Failed to add feedback")
            return False
    except Exception as e:
        print(f"✗ Error adding feedback: {e}")
        return False
    
    # Test retrieving all feedback
    print("\n3. Testing retrieving all feedback...")
    try:
        all_feedback = feedback_db.get_all_feedback()
        print(f"✓ Retrieved {len(all_feedback)} feedback items")
        
        # Print the most recent feedback item
        if all_feedback:
            latest = all_feedback[0]
            print(f"  Latest feedback: ID={latest['id']}, User={latest['user_id']}, Text='{latest['feedback_text'][:30]}...'")
    except Exception as e:
        print(f"✗ Error retrieving feedback: {e}")
        return False
    
    # Test retrieving user feedback
    print("\n4. Testing retrieving user feedback...")
    try:
        user_feedback = feedback_db.get_user_feedback(test_user_id)
        print(f"✓ Retrieved {len(user_feedback)} feedback items for user {test_user_id}")
    except Exception as e:
        print(f"✗ Error retrieving user feedback: {e}")
        return False
    
    # Test adding multiple feedback items
    print("\n5. Testing adding multiple feedback items...")
    try:
        num_items = 5
        for i in range(num_items):
            feedback_text = generate_random_feedback()
            success = feedback_db.add_feedback(test_user_id, feedback_text)
            if not success:
                print(f"✗ Failed to add feedback item {i+1}")
                return False
        print(f"✓ Added {num_items} random feedback items successfully")
    except Exception as e:
        print(f"✗ Error adding multiple feedback items: {e}")
        return False
    
    print("\n✓ All database tests passed!")
    return True

def test_database_performance():
    """Test database performance with a larger number of operations"""
    print("\nTesting database performance...")
    
    try:
        # Add a larger number of feedback items
        num_items = 100
        test_user_id = 987654321
        
        start_time = datetime.now()
        
        for i in range(num_items):
            feedback_text = generate_random_feedback(random.randint(20, 200))
            feedback_db.add_feedback(test_user_id, feedback_text)
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✓ Added {num_items} feedback items in {duration:.2f} seconds")
        print(f"  Average time per item: {(duration/num_items)*1000:.2f} ms")
        
        # Test retrieval performance
        start_time = datetime.now()
        user_feedback = feedback_db.get_user_feedback(test_user_id)
        end_time = datetime.now()
        retrieval_duration = (end_time - start_time).total_seconds()
        
        print(f"✓ Retrieved {len(user_feedback)} feedback items in {retrieval_duration:.2f} seconds")
        
        return True
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False

if __name__ == "__main__":
    print("Database Test Script")
    print("====================")
    
    print(f"Database path: {feedback_db.db_path}")
    
    # Run basic tests
    basic_tests_passed = test_database_operations()
    
    if basic_tests_passed:
        # Ask if user wants to run performance tests
        response = input("\nRun performance tests? (y/n): ")
        if response.lower() == 'y':
            performance_tests_passed = test_database_performance()
        else:
            print("Performance tests skipped.")
    
    # Close database connection
    feedback_db.close()
    print("\nTests completed. Database connection closed.")