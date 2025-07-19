from typing import Optional, Dict, List

# === Prompt Engineering ===
def build_prompt(user_input: str, context: Optional[str] = None) -> List[Dict]:
    """
    Constructs the message list for the API with enhanced context handling.
    """
    system_prompt = (
        "You are a world-class prompt engineer. Your task is to enhance raw user input into "
        "a detailed, structured prompt for an AI model. Consider the following guidelines:\n"
        "1. Identify the user's goal and required output format\n"
        "2. Specify the AI's role and constraints\n"
        "3. Add relevant context and examples if needed\n"
        "4. Structure the prompt with clear sections\n"
        "5. Ensure the enhanced prompt is actionable and specific\n"
        "6. Make the prompt professional and comprehensive\n"
        "7. Include success criteria when appropriate\n\n"
        "Return ONLY the enhanced prompt in plain text format without any additional commentary, "
        "explanations, or meta-text. Do not include phrases like 'Here's your enhanced prompt:' "
        "or any other wrapper text."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    if context:
        messages.insert(1, {"role": "assistant", "content": context})
    
    return messages