import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === Configuration ===
class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENROUTER_API_KEY_01 = os.getenv("OPENROUTER_API_KEY_01")  # Free mode default
    OPENROUTER_API_KEY_02 = os.getenv("OPENROUTER_API_KEY_02")  # Advanced mode default
    
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODELS = {
        "free": "deepseek/deepseek-r1-0528-qwen3-8b:free",
        "advanced": "anthropic/claude-3-opus",
    }
    
    # API key status tracking
    api_status = {
        "key_01": True,  # Available
        "key_02": True   # Available
    }
    
    @classmethod
    def get_api_key_for_mode(cls, mode: str) -> str:
        """Get the appropriate API key for the given mode with fallback logic."""
        if mode == "free":
            # Try API key 01 first (default for free)
            if cls.api_status["key_01"] and cls.OPENROUTER_API_KEY_01:
                return cls.OPENROUTER_API_KEY_01
            # Fallback to API key 02
            elif cls.api_status["key_02"] and cls.OPENROUTER_API_KEY_02:
                logger.warning("API key 01 unavailable, using API key 02 for free mode")
                return cls.OPENROUTER_API_KEY_02
        else:  # advanced mode
            # Try API key 02 first (default for advanced)
            if cls.api_status["key_02"] and cls.OPENROUTER_API_KEY_02:
                return cls.OPENROUTER_API_KEY_02
            # Fallback to API key 01
            elif cls.api_status["key_01"] and cls.OPENROUTER_API_KEY_01:
                logger.warning("API key 02 unavailable, using API key 01 for advanced mode")
                return cls.OPENROUTER_API_KEY_01
        
        raise ValueError("No API keys available")
    
    @classmethod
    def mark_api_key_failed(cls, api_key: str):
        """Mark an API key as failed."""
        if api_key == cls.OPENROUTER_API_KEY_01:
            cls.api_status["key_01"] = False
            logger.error("API key 01 marked as failed")
        elif api_key == cls.OPENROUTER_API_KEY_02:
            cls.api_status["key_02"] = False
            logger.error("API key 02 marked as failed")
    
    @classmethod
    def reset_api_status(cls):
        """Reset API key status (call periodically to retry failed keys)."""
        cls.api_status = {"key_01": True, "key_02": True}
    
    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        if not cls.OPENROUTER_API_KEY_01 and not cls.OPENROUTER_API_KEY_02:
            raise ValueError("At least one OPENROUTER_API_KEY must be provided")
        
        # Log available API keys
        keys_available = []
        if cls.OPENROUTER_API_KEY_01:
            keys_available.append("API_KEY_01")
        if cls.OPENROUTER_API_KEY_02:
            keys_available.append("API_KEY_02")
        
        logger.info(f"Available API keys: {', '.join(keys_available)}")

# === Setup logging ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)