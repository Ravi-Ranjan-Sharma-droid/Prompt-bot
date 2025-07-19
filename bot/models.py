from typing import Dict, List
from datetime import datetime
from bot.config import Config

# === Data Models ===
class UserSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.history: List[Dict] = []
        self.preferred_model: str = Config.MODELS["free"]  # Default to free model
        self.last_interaction: datetime = datetime.now()
        self.feedback_history: List[Dict] = []
    
    def add_to_history(self, original: str, enhanced: str, model_used: str = None):
        """Add a new entry to the user's history"""
        self.history.append({
            "original": original,
            "enhanced": enhanced,
            "model_used": model_used or "unknown",
            "timestamp": datetime.now().isoformat()
        })
        # Keep only the last 20 items
        if len(self.history) > 20:
            self.history = self.history[-20:]
        self.last_interaction = datetime.now()
    
    def add_feedback(self, feedback: str):
        """Add feedback to user's feedback history"""
        self.feedback_history.append({
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only the last 50 feedback items
        if len(self.feedback_history) > 50:
            self.feedback_history = self.feedback_history[-50:]

# Global session storage (in production, use a database)
user_sessions: Dict[int, UserSession] = {}

def get_user_session(user_id: int) -> UserSession:
    """Get or create a user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    return user_sessions[user_id]