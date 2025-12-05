"""
Greeting Agent
Handles initial greeting, name capture, and language selection
"""
from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GreetingAgent(BaseAgent):
    """Agent for welcoming users and collecting basic information"""

    def __init__(self):
        super().__init__("greeting")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process greeting and collect user name"""

        # Mark as visited
        state = self._update_visited_agents(state)

        # Check if user has already been greeted
        if self._get_user_info(state, "greeted"):
            return state

        # Check if we have user's name
        user_name = self._get_user_info(state, "name")

        if not user_name:
            # First interaction - ask for name
            greeting = """Hello! Welcome to Parul University Admission Helpline.
I'm your AI admission assistant, here to help you with any questions about courses, fees, admission process, and scholarships.

May I know your name?"""

            state = self._add_message(state, greeting)
            state = self._set_user_info(state, "greeted", True)
            state = self._set_context(state, "waiting_for_name", True)

        else:
            # We have the name, ask about their interest
            greeting = f"""Nice to meet you, {user_name}! I'm here to help you with information about:

- Courses and Programs
- Fees and Payment Options
- Admission Process and Requirements
- Scholarships and Financial Aid

How can I assist you today?"""

            state = self._add_message(state, greeting)
            state = self._set_context(state, "waiting_for_name", False)
            state = self._set_context(state, "ready_for_inquiry", True)

        return state

    def extract_name_from_message(self, message: str) -> str:
        """
        Extract name from user message
        Simple extraction - looks for common patterns
        """
        message = message.strip()

        # Remove common prefixes
        prefixes = ["my name is", "i am", "i'm", "this is", "call me", "it's", "its"]
        message_lower = message.lower()

        for prefix in prefixes:
            if message_lower.startswith(prefix):
                name = message[len(prefix):].strip()
                # Take first word as name
                return name.split()[0].capitalize() if name else message.split()[0].capitalize()

        # If no prefix, take first word
        words = message.split()
        if words:
            return words[0].capitalize()

        return "Friend"  # Default fallback
