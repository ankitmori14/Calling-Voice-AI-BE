"""
Base Agent Interface
All agents inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all LangGraph agents"""

    def __init__(self, name: str):
        self.name = name
        logger.info(f"Initialized {self.name} agent")

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and return updated state

        Args:
            state: Current conversation state

        Returns:
            Updated state dictionary
        """
        pass

    def _add_message(self, state: Dict[str, Any], content: str, role: str = "assistant") -> Dict[str, Any]:
        """Helper to add a message to state"""
        if "messages" not in state:
            state["messages"] = []

        state["messages"].append({
            "role": role,
            "content": content
        })

        return state

    def _get_user_info(self, state: Dict[str, Any], key: str, default=None):
        """Helper to get user info from state"""
        return state.get("user_info", {}).get(key, default)

    def _set_user_info(self, state: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
        """Helper to set user info in state"""
        if "user_info" not in state:
            state["user_info"] = {}

        state["user_info"][key] = value
        return state

    def _get_context(self, state: Dict[str, Any], key: str, default=None):
        """Helper to get context from state"""
        return state.get("context", {}).get(key, default)

    def _set_context(self, state: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
        """Helper to set context in state"""
        if "context" not in state:
            state["context"] = {}

        state["context"][key] = value
        return state

    def _update_visited_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mark this agent as visited"""
        if "visited_agents" not in state:
            state["visited_agents"] = []

        if self.name not in state["visited_agents"]:
            state["visited_agents"].append(self.name)

        return state
