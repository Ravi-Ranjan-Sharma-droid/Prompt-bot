# Admin Handlers Documentation

## Overview

This document provides detailed information about the admin functionality in the Telegram Prompt Enhancement Bot. Admin handlers are special command handlers that are only accessible to users whose Telegram IDs are listed in the `ADMIN_IDS` environment variable.

## Admin Commands

### `/export_feedback`

**Purpose**: Export all feedback data to a CSV file.

**Implementation**: 
- Located in `admin.py`
- Retrieves all feedback from the database
- Creates a CSV file with columns: ID, User ID, Username, Feedback, Timestamp
- Sanitizes usernames before including them in the export
- Sends the CSV as a document attachment to the admin

**Security**:
- Checks if the user's ID is in the `Config.ADMIN_IDS` list
- Logs unauthorized access attempts
- Sanitizes usernames to prevent CSV injection attacks

**Example Usage**:
```
/export_feedback
```

### `/feedback_stats`

**Purpose**: Display statistics about collected feedback.

**Implementation**:
- Located in `stats.py`
- Calculates various statistics about the feedback data:
  - Total feedback count
  - Feedback received in the last 7 days
  - Number of unique users
  - Percentage of feedback with usernames
  - Number of unique usernames
- Formats the statistics in an HTML-formatted message

**Security**:
- Checks if the user's ID is in the `Config.ADMIN_IDS` list
- Logs unauthorized access attempts

**Example Usage**:
```
/feedback_stats
```

## Admin Configuration

### Setting Up Admin Access

To grant admin access to specific users, add their Telegram user IDs to the `ADMIN_IDS` environment variable in the `.env` file:

```
ADMIN_IDS=123456789,987654321
```

Multiple admin IDs can be specified as a comma-separated list.

### Finding Your Telegram User ID

Users can find their Telegram ID by:
1. Messaging the [@userinfobot](https://t.me/userinfobot) on Telegram
2. Using the `/id` command with [@RawDataBot](https://t.me/RawDataBot)

## Database Integration

Admin commands interact with the feedback database (`feedback_db`) defined in `database.py`. The database provides methods for:

- `get_all_feedback()`: Retrieves all feedback entries
- `get_user_feedback(user_id)`: Retrieves feedback from a specific user

## Security Considerations

1. **Access Control**: All admin commands verify the user's ID against the `ADMIN_IDS` list before execution
2. **Logging**: Unauthorized access attempts are logged with warning level
3. **Input Sanitization**: Usernames are sanitized before being included in exports
4. **Error Handling**: All database operations are wrapped in try-except blocks to prevent crashes

## Future Enhancements

Potential improvements for admin functionality:

1. **User Management**: Add commands to block/unblock users
2. **Broadcast Messages**: Add ability to send announcements to all users
3. **Advanced Analytics**: Implement more detailed feedback analysis
4. **Web Dashboard**: Create a web interface for admin functions

## Troubleshooting

- If admin commands aren't working, verify that your Telegram user ID is correctly added to the `ADMIN_IDS` environment variable
- Check the logs for any errors related to admin command execution
- Ensure the database connection is working properly