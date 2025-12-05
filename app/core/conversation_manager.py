"""
Conversation Manager
Manages conversation state with memory persistence
"""
import uuid
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from app.core.langgraph_workflow import get_workflow
from app.memory.conversation_memory import get_conversation_memory
from app.memory.user_memory import get_user_memory
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationManager:
    """Manages conversations with memory persistence"""

    def __init__(self):
        self.workflow = get_workflow()
        self.conversation_memory = get_conversation_memory()
        self.user_memory = get_user_memory()
        logger.info("Initialized Conversation Manager")

    async def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation session"""

        session_id = str(uuid.uuid4())

        # Initialize session state
        initial_state = {
            "session_id": session_id,
            "messages": [],
            "user_info": {},
            "context": {},
            "visited_agents": [],
            "topics_discussed": [],
            "conversation_count": 0
        }

        # Load user profile if exists
        if user_id:
            user_profile = await self.user_memory.get_user(user_id)
            if user_profile:
                initial_state["user_info"]["name"] = user_profile.get("name")
                initial_state["user_info"]["user_id"] = user_id
                logger.info(f"Loaded existing user profile for {user_id}")

        # Save initial state
        await self.conversation_memory.save_state(session_id, initial_state)

        logger.info(f"Created new session: {session_id}")
        return session_id

    async def process_message(self, session_id: str, user_message: str) -> str:
        """
        Process a user message and return assistant's response

        Args:
            session_id: Session identifier
            user_message: User's message text

        Returns:
            Assistant's response text
        """

        logger.info(f"Processing message for session {session_id}: {user_message[:50]}...")

        # Get existing state
        existing_state = await self.conversation_memory.get_state(session_id)

        # Process through workflow
        updated_state = await self.workflow.process_message(session_id, user_message, existing_state)

        # Save updated state
        await self.conversation_memory.save_state(session_id, updated_state)

        # Add messages to conversation history
        await self.conversation_memory.add_message(session_id, "user", user_message)

        # Get assistant's response (last message)
        messages = updated_state.get("messages", [])
        assistant_message = ""

        for msg in reversed(messages):
            # Handle both dict and LangChain message objects
            if isinstance(msg, (AIMessage, BaseMessage)):
                if isinstance(msg, AIMessage):
                    assistant_message = msg.content
                    break
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                assistant_message = msg.get("content", "")
                break

        if assistant_message:
            await self.conversation_memory.add_message(session_id, "assistant", assistant_message)

        # Update user profile if we have new information
        user_info = updated_state.get("user_info", {})
        if user_info.get("name") or user_info.get("email") or user_info.get("phone"):
            await self._update_user_profile(session_id, user_info)

        logger.info(f"Completed processing for session {session_id}")

        return assistant_message

    async def _update_user_profile(self, session_id: str, user_info: Dict[str, Any]):
        """Update user profile with new information"""

        # Use phone or email as user_id if available
        user_id = user_info.get("phone") or user_info.get("email") or session_id

        # Check if user exists
        existing_user = await self.user_memory.get_user(user_id)

        if existing_user:
            # Update existing user
            for key, value in user_info.items():
                if value:  # Only update non-empty values
                    await self.user_memory.update_user_field(user_id, key, value)
        else:
            # Create new user profile
            user_profile = {
                "user_id": user_id,
                **user_info
            }
            await self.user_memory.save_user(user_id, user_profile)

        logger.debug(f"Updated user profile for {user_id}")

    async def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> list:
        """Get conversation history for a session"""
        return await self.conversation_memory.get_messages(session_id, limit)

    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state"""
        return await self.conversation_memory.get_state(session_id)

    async def end_session(self, session_id: str):
        """End a conversation session"""
        # Don't delete, just mark as ended
        state = await self.conversation_memory.get_state(session_id)
        if state:
            state["ended"] = True
            await self.conversation_memory.save_state(session_id, state)
        logger.info(f"Ended session: {session_id}")


# Global manager instance
_manager_instance = None


def get_conversation_manager() -> ConversationManager:
    """Get global conversation manager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ConversationManager()
    return _manager_instance
