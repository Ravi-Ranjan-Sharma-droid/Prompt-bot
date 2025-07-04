# AI Prompt Enhancer Bot

## Overview

AI Prompt Enhancer Bot is a Telegram bot that transforms simple user inputs into detailed, structured prompts optimized for AI models. The bot leverages OpenRouter API to access various AI models and provides an interactive interface for users to enhance their prompts.

## Features

- **Prompt Enhancement**: Transform simple ideas into detailed, structured prompts
- **Dual Model Support**: Choose between Free (faster) and Advanced (higher quality) models
- **Interactive UI**: Easy-to-use Telegram interface with buttons and menus
- **User History**: Track and review your enhanced prompts
- **Feedback System**: Submit feedback to help improve the bot
- **API Fallback**: Automatic fallback between API keys if one fails


## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/AI-prompt.git
cd AI-prompt
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
OPENROUTER_API_KEY_01=API_KEY
OPENROUTER_API_KEY_02=API_KEY
```


## Usage

### Starting the bot

```bash
python main.py
```

### Telegram Commands

- `/start` - Main menu
- `/help` - Show help message
- `/history` - View your recent prompts
- `/model` - Switch between different AI models
- `/feedback` - Send feedback or report issues
- `/status` - Check bot and API status

### How to Use

1. Start a chat with your bot on Telegram
2. Send any idea, question, or goal
3. The bot will transform it into a detailed, structured prompt
4. Use the enhanced prompt with any AI model for better results

## Configuration Options

The bot offers two modes:

- **Free Mode**: Uses a smaller, faster model (default: deepseek/deepseek-r1-0528-qwen3-8b:free)
- **Advanced Mode**: Uses a more powerful model (default: anthropic/claude-3-opus)

Users can switch between these modes using the settings menu or the `/model` command.

## Troubleshooting

- If you don't receive responses, check the API status with `/status`
- If an API key fails, the bot will automatically try to use the other key
- You can reset API status through the settings menu
- For persistent issues, use the `/feedback` command to report problems

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or feedback, you can find the developer on Instagram: [@nr_snorlax](https://www.instagram.com/nr_snorlax/)