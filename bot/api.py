import requests
import logging
from typing import Dict, List, Tuple

from bot.config import Config

logger = logging.getLogger(__name__)

# === API Communication ===
async def ask_openrouter(messages: List[Dict], model: str, mode: str = "free") -> Tuple[str, str]:
    """
    Enhanced API communication with dual API key support and fallback logic.
    Returns: (response_text, model_used)
    """
    max_retries = 2
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Get appropriate API key
            api_key = Config.get_api_key_for_mode(mode)
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",
                "X-Title": "Advanced Prompt Enhancer Bot"
            }

            data = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }

            response = requests.post(
                Config.OPENROUTER_URL,
                headers=headers,
                json=data,
                timeout=45
            )
            
            if response.status_code == 401:
                # API key is invalid, mark it as failed
                Config.mark_api_key_failed(api_key)
                raise Exception("API key authentication failed")
            
            response.raise_for_status()
            
            result = response.json()
            if not result.get("choices"):
                raise ValueError("Unexpected API response format")
            
            # Determine which model was actually used
            model_used = result.get("model", model)
            
            return result["choices"][0]["message"]["content"], model_used
    
        except requests.exceptions.Timeout:
            logger.error(f"OpenRouter API timeout (attempt {attempt + 1})")
            last_error = "The AI service is taking too long to respond. Please try again."
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed (attempt {attempt + 1}): {str(e)}")
            last_error = f"Failed to communicate with the AI service: {str(e)}"
        except ValueError as e:
            logger.error(f"API response parsing failed (attempt {attempt + 1}): {str(e)}")
            last_error = "Received an unexpected response from the AI service."
        except Exception as e:
            logger.error(f"Unexpected error (attempt {attempt + 1}): {str(e)}")
            last_error = str(e)
            
            # If this was the last attempt, check if we can try with the other API key
            if attempt == max_retries - 1:
                # If we're using key_01 and key_02 is available, try again with key_02
                if mode == "free" and Config.api_status["key_02"] and Config.OPENROUTER_API_KEY_02:
                    Config.mark_api_key_failed(api_key)  # Mark current key as failed
                    logger.info("Retrying with API key 02 as fallback")
                    try:
                        return await ask_openrouter(messages, model, "advanced")
                    except Exception as inner_e:
                        last_error = str(inner_e)
                # If we're using key_02 and key_01 is available, try again with key_01
                elif mode == "advanced" and Config.api_status["key_01"] and Config.OPENROUTER_API_KEY_01:
                    Config.mark_api_key_failed(api_key)  # Mark current key as failed
                    logger.info("Retrying with API key 01 as fallback")
                    try:
                        return await ask_openrouter(messages, model, "free")
                    except Exception as inner_e:
                        last_error = str(inner_e)
    
    # If all retries failed, raise the last error
    raise Exception(last_error or "Failed to get response from AI service")