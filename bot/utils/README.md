# Utilities Module

This module contains utility functions used throughout the Prompt-bot application.

## Username Utilities

### `format_username(user)`

Formats a consistent username from a Telegram user object.

**Parameters:**
- `user`: The Telegram user object

**Returns:**
- A formatted username string

**Behavior:**
1. If `user.username` exists, it is returned
2. Otherwise, a full name is constructed from `first_name` and `last_name`
3. If no name information is available, returns `User_{user.id}`

### `sanitize_username(username, max_length=100)`

Sanitizes a username to ensure it's safe for storage.

**Parameters:**
- `username`: The username to sanitize
- `max_length`: Maximum allowed length for username (default: 100)

**Returns:**
- Sanitized username or None if input was None

**Behavior:**
1. Returns None if input is None
2. Truncates usernames longer than `max_length`
3. Removes leading and trailing whitespace

## Usage Examples

```python
from telegram import Update
from bot.utils import format_username, sanitize_username

# In a message handler
async def handle_message(update: Update, context):
    user = update.effective_user
    username = format_username(user)
    
    # Sanitize before storing
    safe_username = sanitize_username(username)
    
    # Use the username
    print(f"Message from {safe_username}")
```

## Best Practices

1. Always use `format_username()` when extracting usernames from Telegram user objects
2. Always use `sanitize_username()` before storing usernames in the database
3. Consider case sensitivity when comparing usernames
4. Handle None values appropriately when working with usernames