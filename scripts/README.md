# Analysis Scripts

This directory contains utility scripts for analyzing data from the Telegram Prompt Enhancement Bot.

## Available Scripts

### test_database.py

This script tests the feedback database implementation to ensure it's working correctly.

#### Features

- Tests database initialization
- Tests adding and retrieving feedback
- Tests user-specific feedback retrieval
- Optional performance testing with larger datasets

#### Usage

```bash
# Run the test script
python test_database.py
```

### backup_database.py

This script creates a backup of the feedback database and manages backup retention.

#### Features

- Creates timestamped backups of the SQLite database
- Uses SQLite's native backup API for reliable backups
- Falls back to file copy method if native backup fails
- Automatically cleans up backups older than 30 days
- Verifies backup integrity

#### Usage

```bash
# Create backup in default location (project_root/backups/)
python backup_database.py

# Create backup in custom location
python backup_database.py /path/to/backup/directory
```

### restore_database.py

This script restores the feedback database from a backup file.

#### Features

- Lists available backups with timestamps and sizes
- Creates a safety backup of the current database before restoring
- Uses SQLite's native backup API for reliable restoration
- Falls back to file copy method if native restore fails
- Verifies the restored database integrity

#### Usage

```bash
# List available backups and select one to restore
python restore_database.py

# Restore from a specific backup file
python restore_database.py /path/to/backup/file.db
```

#### Scheduling Regular Backups

**On Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create a new Basic Task
3. Set trigger (e.g., Daily at 3:00 AM)
4. Set action: Start a program
5. Program/script: `python`
6. Arguments: `scripts/backup_database.py`
7. Start in: `your_project_directory`

**On Linux/macOS (Cron):**
```bash
# Edit crontab
crontab -e

# Add line to run daily at 3:00 AM
0 3 * * * cd /path/to/project && python scripts/backup_database.py
```

### migrate_feedback.py

This script migrates existing in-memory feedback to the SQLite database. It's useful when upgrading from a version without database support.

#### Features

- Migrates all in-memory feedback to the SQLite database
- Verifies migration success
- Provides a summary of migrated items

#### Usage

```bash
# Run the script
python migrate_feedback.py
```

### analyze_feedback.py

This script demonstrates how to analyze feedback data stored in the SQLite database.

#### Features

- Loads feedback data from the database
- Generates basic statistics (total entries, unique users, date range)
- Creates visualizations of feedback submission patterns:
  - Submissions by day of week
  - Submissions by hour of day
- Performs simple word frequency analysis

#### Requirements

- pandas
- matplotlib

#### Usage

```bash
# Install dependencies
pip install pandas matplotlib

# Run the script
python analyze_feedback.py
```

#### Output

The script will generate:

1. Console output with statistics
2. Two PNG image files:
   - `feedback_by_day.png` - Bar chart of submissions by day of week
   - `feedback_by_hour.png` - Bar chart of submissions by hour of day

### migrate_username.py

This script updates the feedback database schema to include a username field for better user identification in feedback.

#### Features

- Checks if migration is needed by examining the database schema
- Creates a backup of the database before making any changes
- Adds the username column to the feedback table
- Verifies the migration was successful
- Provides detailed logging and user feedback

#### Usage

```bash
# Run the migration script
python migrate_username.py
```

### test_username.py

This script tests the username field functionality in the feedback database by adding test entries and verifying they are stored correctly.

#### Features

- Tests adding feedback with username
- Tests retrieving user feedback with username
- Verifies that username data is correctly stored and retrieved
- Creates and uses a temporary test database to avoid affecting production data

#### Usage

```bash
# Run the username tests
python test_username.py
```

## Adding New Scripts

When adding new analysis scripts to this directory, please follow these guidelines:

1. Include a descriptive docstring at the top of the file
2. Add error handling for missing dependencies
3. Document the script in this README
4. Use relative imports when accessing the bot's modules