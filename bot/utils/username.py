"""Username utilities for the Prompt-bot application.

This module provides functions for formatting and sanitizing usernames.
"""

from typing import Optional
from telegram import User

def format_username(user: User) -> str:
    """Format a consistent username from a Telegram user object.
    
    Args:
        user: The Telegram user object
        
    Returns:
        A formatted username string
    """
    if user.username:
        return user.username
    
    full_name = f"{user.first_name} {user.last_name if user.last_name else ''}".strip()
    if full_name:
        return full_name
    
    return f"User_{user.id}"

def sanitize_username(username: Optional[str], max_length: int = 100) -> Optional[str]:
    """Sanitize a username to ensure it's safe for storage.
    
    Args:
        username: The username to sanitize
        max_length: Maximum allowed length for username
        
    Returns:
        Sanitized username or None if input was None
    """
    if username is None:
        return None
        
    # Truncate long usernames
    if len(username) > max_length:
        username = username[:max_length]
    
    # Remove any potentially problematic characters
    # This is a simple example - you might want to customize based on your needs
    return username.strip()