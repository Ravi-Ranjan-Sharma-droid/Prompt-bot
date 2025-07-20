# Telegram Prompt Enhancement Bot

## Overview

The Telegram Prompt Enhancement Bot is a powerful tool designed to transform simple user inputs into detailed, structured prompts optimized for AI models. This bot provides an interactive Telegram interface that helps users create better prompts for their AI interactions.

## Features

- **Prompt Enhancement**: Transform simple ideas into detailed, structured prompts with clear instructions and context
- **Dual Model Support**: Choose between Free (faster) and Advanced (higher quality) models for different needs
- **Interactive UI**: Easy-to-use Telegram interface with buttons and menus for seamless navigation
- **User History**: Track and review your enhanced prompts with timestamps and model information
- **Feedback System**: Submit feedback to help improve the bot's functionality
- **Automatic Fallback**: Intelligent fallback between available AI services if one experiences issues
- **Modular Architecture**: Clean, maintainable codebase with separation of concerns

## Project Structure

```
project-root/
├── bot/                      # Core logic
│   ├── __init__.py
│   ├── config.py            # Configuration and env loading
│   ├── models.py            # Data models (e.g., UserSession)
│   ├── prompts.py           # Prompt engineering logic
│   ├── api.py               # API communication
│   ├── handlers/            # Telegram handlers
│   │   ├── __init__.py
│   │   ├── commands.py      # /start, /help, /feedback, etc.
│   │   ├── messages.py      # Message handler
│   │   ├── callbacks.py     # Button and callback queries
│   │   └── errors.py        # Error handling
│   └── tasks.py             # Periodic jobs like cleanup
├── main.py                  # Starts the bot, loads handlers
├── requirements.txt         # Project dependencies
├── .env                     # Environment variables (not in repo)
└── README.md                # This file
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/prompt-bot.git
cd prompt-bot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

#### Activate the virtual environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root with the following variables:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# Add your API keys for the AI services
```

## Usage

### Starting the bot

```bash
python main.py
```

### Telegram Commands

- `/start` - Display the main menu with interactive buttons
- `/help` - Show detailed help message and command list
- `/history` - View your recent prompts and their enhanced versions
- `/model` - Switch between Free and Advanced AI models
- `/feedback` - Send feedback or report issues
- `/status` - Check bot status and service availability

### How to Use

1. Start a chat with your bot on Telegram
2. Send any idea, question, or goal you want to transform into a better prompt
3. The bot will process your input and return an enhanced, structured prompt
4. Use the interactive buttons to:
   - Further improve the prompt
   - View your prompt history
   - Access settings and change models
   - Get help with using the bot

## Configuration Options

The bot offers two modes:

- **Free Model**: Uses a smaller, faster model (Deepseek)
  - Fast response times
  - Good for basic prompt enhancement
  - No usage limits

- **Advanced Model**: Uses a more powerful model (Claude)
  - Superior quality outputs
  - Better understanding of complex requests
  - More creative and detailed enhancements

Users can switch between these modes using the settings menu or the `/model` command.

## Periodic Tasks

The bot performs these maintenance tasks automatically:

- Removing user sessions inactive for more than 7 days
- Resetting API status hourly to recover from temporary issues
- Maintaining database connections and verifying feedback storage

## Feedback Database

The bot now stores all user feedback in an SQLite database (`feedback.db`) for better persistence and analysis:

### Features

- All feedback is automatically saved to both in-memory storage and the SQLite database
- Dual storage ensures compatibility with existing code while adding persistence
- Admin commands are available for feedback management:
  - `/export_feedback` - Export all feedback to a CSV file
  - `/feedback_stats` - View statistics about collected feedback
- Configure admin access by setting the `ADMIN_IDS` environment variable with comma-separated Telegram user IDs

### Database Schema

The feedback database uses a simple schema:

```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    feedback_text TEXT NOT NULL,
    timestamp TEXT NOT NULL
)
```

### Utility Scripts

The `scripts/` directory contains utility scripts for working with the feedback database:

- `migrate_feedback.py` - Migrate existing in-memory feedback to the database
- `analyze_feedback.py` - Generate statistics and visualizations from feedback data
- `backup_database.py` - Create and manage database backups

See the [scripts README](scripts/README.md) for more information.

## Troubleshooting

- If you don't receive responses, check the service status with `/status`
- If one service is unavailable, the bot will automatically try to use an alternative
- You can reset service status through the settings menu
- For persistent issues, use the `/feedback` command to report problems

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or feedback, you can find the developer on Instagram: [@nr_snorlax](https://www.instagram.com/nr_snorlax/)