#!/usr/bin/env python
"""
Test script for username utilities

This script tests the username formatting and sanitization utilities
to ensure they work correctly with various inputs.

Usage:
    python test_username_utils.py
"""

import sys
import os
import unittest
from unittest.mock import MagicMock

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the utilities to test
from bot.utils.username import format_username, sanitize_username

class TestUsernameUtils(unittest.TestCase):
    """Test cases for username utilities"""
    
    def test_format_username_with_username(self):
        """Test format_username with a user that has a username"""
        # Create a mock User object
        user = MagicMock()
        user.username = "test_user"
        user.first_name = "Test"
        user.last_name = "User"
        user.id = 12345
        
        # Test that username is used when available
        self.assertEqual(format_username(user), "test_user")
    
    def test_format_username_with_full_name(self):
        """Test format_username with a user that has first and last name"""
        # Create a mock User object with no username
        user = MagicMock()
        user.username = None
        user.first_name = "Test"
        user.last_name = "User"
        user.id = 12345
        
        # Test that full name is used when username is not available
        self.assertEqual(format_username(user), "Test User")
    
    def test_format_username_with_first_name_only(self):
        """Test format_username with a user that has only first name"""
        # Create a mock User object with no username and no last name
        user = MagicMock()
        user.username = None
        user.first_name = "Test"
        user.last_name = None
        user.id = 12345
        
        # Test that first name is used when username and last name are not available
        self.assertEqual(format_username(user), "Test")
    
    def test_format_username_with_no_name(self):
        """Test format_username with a user that has no name information"""
        # Create a mock User object with no username and no names
        user = MagicMock()
        user.username = None
        user.first_name = None
        user.last_name = None
        user.id = 12345
        
        # Test that user ID is used when no name information is available
        self.assertEqual(format_username(user), "User_12345")
    
    def test_sanitize_username_normal(self):
        """Test sanitize_username with normal input"""
        self.assertEqual(sanitize_username("normal_username"), "normal_username")
    
    def test_sanitize_username_with_spaces(self):
        """Test sanitize_username with spaces"""
        self.assertEqual(sanitize_username("username with spaces"), "username with spaces")
    
    def test_sanitize_username_with_leading_trailing_spaces(self):
        """Test sanitize_username with leading/trailing spaces"""
        self.assertEqual(sanitize_username("  username  "), "username")
    
    def test_sanitize_username_too_long(self):
        """Test sanitize_username with a username that exceeds max length"""
        long_username = "a" * 150
        self.assertEqual(len(sanitize_username(long_username)), 100)
    
    def test_sanitize_username_none(self):
        """Test sanitize_username with None input"""
        self.assertIsNone(sanitize_username(None))
    
    def test_sanitize_username_custom_max_length(self):
        """Test sanitize_username with custom max length"""
        long_username = "a" * 50
        self.assertEqual(len(sanitize_username(long_username, max_length=30)), 30)

if __name__ == "__main__":
    unittest.main()