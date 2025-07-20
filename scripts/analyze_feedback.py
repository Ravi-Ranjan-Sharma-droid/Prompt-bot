#!/usr/bin/env python
"""
Feedback Analysis Script

This script demonstrates how to directly query the feedback database
for advanced analysis outside of the bot application.

Usage:
    python analyze_feedback.py
"""

import sqlite3
import sys
import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from typing import Set, Dict, List, Optional, Tuple, Counter as CounterType

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import bot modules (optional, can use direct SQLite connection instead)
from bot.database import feedback_db

# Try to import utils module for username handling
try:
    from bot.utils.username import sanitize_username
except ImportError:
    # Fallback implementation if module not available
    def sanitize_username(username, max_length=100):
        """Fallback implementation of sanitize_username"""
        if username is None:
            return None
        if len(username) > max_length:
            username = username[:max_length]
        return username.strip()

def analyze_username_patterns(df: pd.DataFrame) -> None:
    """Analyze patterns in usernames and provide recommendations
    
    Args:
        df: DataFrame containing feedback data with username column
    """
    print("\n===== USERNAME PATTERN ANALYSIS =====")
    
    # Get non-null usernames
    valid_usernames = df['username'].dropna().tolist()
    
    if not valid_usernames:
        print("No valid usernames found for analysis.")
        return
    
    # Apply sanitization to all usernames
    sanitized_usernames = [sanitize_username(username) for username in valid_usernames]
    sanitized_usernames = [u for u in sanitized_usernames if u]  # Remove any that became empty
    
    # Analyze username patterns
    username_lengths = [len(username) for username in sanitized_usernames]
    avg_length = sum(username_lengths) / len(username_lengths) if username_lengths else 0
    
    # Check for potential patterns
    has_numeric_suffix = sum(1 for u in sanitized_usernames if re.search(r'_\d+$', u))
    has_spaces = sum(1 for u in sanitized_usernames if ' ' in u)
    has_special_chars = sum(1 for u in sanitized_usernames if re.search(r'[^\w\s]', u))
    
    # Print analysis
    print(f"Average username length: {avg_length:.1f} characters")
    print(f"Usernames with numeric suffixes: {has_numeric_suffix} ({has_numeric_suffix/len(sanitized_usernames)*100:.1f}%)")
    print(f"Usernames with spaces: {has_spaces} ({has_spaces/len(sanitized_usernames)*100:.1f}%)")
    print(f"Usernames with special characters: {has_special_chars} ({has_special_chars/len(sanitized_usernames)*100:.1f}%)")
    
    # Provide recommendations
    print("\nRecommendations for username handling:")
    if has_spaces > 0:
        print("- Consider normalizing usernames with spaces (e.g., replace with underscores)")
    if has_special_chars > 0:
        print("- Consider sanitizing special characters in usernames")
    if avg_length > 20:
        print("- Consider truncating long usernames for display purposes")
    
    # Check for potential duplicates with different casing
    lowercase_map = {}
    for username in sanitized_usernames:
        lower = username.lower()
        if lower in lowercase_map:
            lowercase_map[lower].append(username)
        else:
            lowercase_map[lower] = [username]
    
    # Find duplicates with different casing
    case_duplicates = {k: v for k, v in lowercase_map.items() if len(v) > 1}
    if case_duplicates:
        print("- Consider case-insensitive username comparisons to avoid duplicates")
        print(f"  Found {len(case_duplicates)} potential case-sensitive duplicates")


def analyze_feedback_direct():
    """Analyze feedback using direct database connection"""
    try:
        # Connect to the database
        conn = sqlite3.connect('../feedback.db')
        
        # Check if username column exists
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(feedback)")
        columns = cursor.fetchall()
        has_username = any(column[1] == 'username' for column in columns)
        
        # Query all feedback
        query = "SELECT * FROM feedback ORDER BY timestamp DESC"
        
        # Load into pandas DataFrame
        df = pd.read_sql_query(query, conn)
        
        # Close connection
        conn.close()
        
        if df.empty:
            print("No feedback data found in database.")
            return
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Username statistics if available
        if has_username and 'username' in df.columns:
            # Clean up usernames - replace None with NaN for better pandas handling
            df['username'] = df['username'].fillna(pd.NA)
            
            # Count entries with valid usernames
            username_count = df['username'].notna().sum()
            username_percentage = username_count/len(df)*100 if len(df) > 0 else 0
            print(f"Feedback entries with username: {username_count} ({username_percentage:.1f}%)")
            
            # Count unique usernames vs unique user IDs
            unique_usernames = df['username'].dropna().nunique()
            unique_user_ids = df['user_id'].nunique()
            username_coverage = unique_usernames/unique_user_ids*100 if unique_user_ids > 0 else 0
            print(f"Unique usernames: {unique_usernames} ({username_coverage:.1f}% of {unique_user_ids} unique users)")
            
            # Add user breakdown for top contributors
            print("\n===== TOP USERS PROVIDING FEEDBACK =====")
            user_counts = df['username'].value_counts().head(10)
            
            # Create a more detailed table format
            print(f"{'Username':<20} | {'Count':<5} | {'Percentage':<10}")
            print("-" * 40)
            
            for username, count in user_counts.items():
                if pd.notna(username):  # Skip NaN usernames
                    percentage = count/len(df)*100
                    print(f"{str(username)[:19]:<20} | {count:<5} | {percentage:.1f}%")
        
        # Basic statistics
        print(f"Total feedback entries: {len(df)}")
        print(f"Unique users: {df['user_id'].nunique()}")
        print(f"Date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
        
        # Feedback by day of week
        df['day_of_week'] = df['timestamp'].dt.day_name()
        day_counts = df['day_of_week'].value_counts()
        
        # Plot feedback by day of week
        plt.figure(figsize=(10, 6))
        day_counts.plot(kind='bar')
        plt.title('Feedback Submissions by Day of Week')
        plt.xlabel('Day of Week')
        plt.ylabel('Number of Submissions')
        plt.tight_layout()
        plt.savefig('feedback_by_day.png')
        print("\nChart saved as 'feedback_by_day.png'")
        
        # Feedback by hour of day
        df['hour'] = df['timestamp'].dt.hour
        hour_counts = df['hour'].value_counts().sort_index()
        
        # Plot feedback by hour
        plt.figure(figsize=(12, 6))
        hour_counts.plot(kind='bar')
        plt.title('Feedback Submissions by Hour of Day')
        plt.xlabel('Hour (24-hour format)')
        plt.ylabel('Number of Submissions')
        plt.xticks(range(24))
        plt.tight_layout()
        plt.savefig('feedback_by_hour.png')
        print("Chart saved as 'feedback_by_hour.png'")
        
        # Word frequency analysis (simple example)
        from collections import Counter
        import re
        
        # Analyze username patterns if available
        if has_username and 'username' in df.columns:
            analyze_username_patterns(df)
        
        # Combine all feedback text
        all_text = ' '.join(df['feedback_text'])
        
        # Split into words and convert to lowercase
        words = re.findall(r'\b\w+\b', all_text.lower())
        
        # Count word frequency
        word_counts = Counter(words)
        
        # Remove common stop words (simplified example)
        stop_words = {'the', 'and', 'is', 'in', 'to', 'a', 'of', 'for', 'that', 'this'}
        for word in stop_words:
            if word in word_counts:
                del word_counts[word]
        
        # Print most common words
        print("\nMost common words in feedback:")
        for word, count in word_counts.most_common(10):
            print(f"{word}: {count}")
            
    except Exception as e:
        print(f"Error analyzing feedback: {e}")

def analyze_feedback_using_module():
    """Analyze feedback using the bot's database module
    
    This function uses the bot's database module to retrieve feedback data
    and performs basic analysis, including username statistics.
    """
    try:
        # Get all feedback using the bot's database module
        all_feedback = feedback_db.get_all_feedback()
        
        if not all_feedback:
            print("No feedback data found in database.")
            return
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(all_feedback)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Print basic statistics
        print(f"Total feedback entries: {len(df)}")
        print(f"Unique users: {df['user_id'].nunique()}")
        print(f"Date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
        
        # Username statistics if available
        if 'username' in df.columns:
            # Clean up usernames
            df['username'] = df['username'].apply(sanitize_username)
            
            # Count entries with valid usernames
            username_count = df['username'].notna().sum()
            username_percentage = username_count/len(df)*100 if len(df) > 0 else 0
            print(f"Feedback entries with username: {username_count} ({username_percentage:.1f}%)")
            
            # Count unique usernames
            unique_usernames = df['username'].dropna().nunique()
            unique_user_ids = df['user_id'].nunique()
            username_coverage = unique_usernames/unique_user_ids*100 if unique_user_ids > 0 else 0
            print(f"Unique usernames: {unique_usernames} ({username_coverage:.1f}% of {unique_user_ids} unique users)")
            
            # Analyze username patterns
            analyze_username_patterns(df)
        
    except Exception as e:
        print(f"Error analyzing feedback using module: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Feedback Analysis Script")
    print("=======================")
    
    # Check if pandas and matplotlib are installed
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
    except ImportError:
        print("Error: This script requires pandas and matplotlib.")
        print("Please install them with: pip install pandas matplotlib")
        sys.exit(1)
    
    # Choose analysis method
    print("\nAnalyzing feedback using direct database connection...")
    analyze_feedback_direct()
    
    print("\nAnalyzing feedback using bot's database module...")
    analyze_feedback_using_module()