"""
JSON-based conversation memory storage
Stores conversation history and state for each session
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
from app.utils.logger import get_logger
from app.models.conversation import ConversationState

logger = get_logger(__name__)


class ConversationMemory:
    """Manage conversation memory using JSON file storage"""

    def __init__(self, file_path: str = "./app/memory/conversations.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._memory: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._load()

    def _load(self):
        """Load conversations from JSON file"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._memory = json.load(f)
                logger.info(f"Loaded {len(self._memory)} conversations from memory")
            except json.JSONDecodeError:
                logger.error("Error loading conversation memory, starting fresh")
                self._memory = {}
        else:
            self._memory = {}
            self._save()

    def _save(self):
        """Save conversations to JSON file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._memory, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving conversation memory: {e}")

    async def save_state(self, session_id: str, state: Dict[str, Any]):
        """Save conversation state"""
        async with self._lock:
            if session_id not in self._memory:
                self._memory[session_id] = {
                    "created_at": datetime.utcnow().isoformat(),
                    "messages": [],
                    "state": {}
                }

            self._memory[session_id]["state"] = state
            self._memory[session_id]["updated_at"] = datetime.utcnow().isoformat()
            self._save()
            logger.debug(f"Saved state for session {session_id}")

    async def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation state"""
        async with self._lock:
            conversation = self._memory.get(session_id)
            if conversation:
                return conversation.get("state")
            return None

    async def add_message(self, session_id: str, role: str, content: str):
        """Add a message to conversation history"""
        async with self._lock:
            if session_id not in self._memory:
                self._memory[session_id] = {
                    "created_at": datetime.utcnow().isoformat(),
                    "messages": [],
                    "state": {}
                }

            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }

            self._memory[session_id]["messages"].append(message)
            self._memory[session_id]["updated_at"] = datetime.utcnow().isoformat()
            self._save()

    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get conversation messages"""
        async with self._lock:
            conversation = self._memory.get(session_id)
            if not conversation:
                return []

            messages = conversation.get("messages", [])
            if limit:
                return messages[-limit:]
            return messages

    async def get_conversation(self, session_id: str) -> Optional[Dict]:
        """Get full conversation data"""
        async with self._lock:
            return self._memory.get(session_id)

    async def delete_conversation(self, session_id: str):
        """Delete a conversation"""
        async with self._lock:
            if session_id in self._memory:
                del self._memory[session_id]
                self._save()
                logger.info(f"Deleted conversation {session_id}")

    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs"""
        async with self._lock:
            return list(self._memory.keys())

    async def clear_old_conversations(self, days: int = 30):
        """Clear conversations older than specified days"""
        async with self._lock:
            cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
            to_delete = []

            for session_id, conv in self._memory.items():
                created_at = datetime.fromisoformat(conv["created_at"]).timestamp()
                if created_at < cutoff_date:
                    to_delete.append(session_id)

            for session_id in to_delete:
                del self._memory[session_id]

            if to_delete:
                self._save()
                logger.info(f"Cleared {len(to_delete)} old conversations")


# Global conversation memory instance
conversation_memory = ConversationMemory()


def get_conversation_memory() -> ConversationMemory:
    """Get global conversation memory instance"""
    return conversation_memory
