"""
JSON-based user memory storage
Stores user profiles and preferences
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from app.utils.logger import get_logger
from app.models.user import UserProfile

logger = get_logger(__name__)


class UserMemory:
    """Manage user memory using JSON file storage"""

    def __init__(self, file_path: str = "./app/memory/users.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._memory: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._load()

    def _load(self):
        """Load users from JSON file"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._memory = json.load(f)
                logger.info(f"Loaded {len(self._memory)} user profiles from memory")
            except json.JSONDecodeError:
                logger.error("Error loading user memory, starting fresh")
                self._memory = {}
        else:
            self._memory = {}
            self._save()

    def _save(self):
        """Save users to JSON file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._memory, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving user memory: {e}")

    async def save_user(self, user_id: str, user_data: Dict):
        """Save or update user profile"""
        async with self._lock:
            if user_id not in self._memory:
                user_data["created_at"] = datetime.utcnow().isoformat()

            user_data["updated_at"] = datetime.utcnow().isoformat()
            self._memory[user_id] = user_data
            self._save()
            logger.debug(f"Saved user profile for {user_id}")

    async def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user profile"""
        async with self._lock:
            return self._memory.get(user_id)

    async def update_user_field(self, user_id: str, field: str, value: any):
        """Update a specific field in user profile"""
        async with self._lock:
            if user_id in self._memory:
                self._memory[user_id][field] = value
                self._memory[user_id]["updated_at"] = datetime.utcnow().isoformat()
                self._save()

    async def user_exists(self, user_id: str) -> bool:
        """Check if user exists"""
        async with self._lock:
            return user_id in self._memory

    async def delete_user(self, user_id: str):
        """Delete user profile"""
        async with self._lock:
            if user_id in self._memory:
                del self._memory[user_id]
                self._save()
                logger.info(f"Deleted user {user_id}")

    async def search_users(self, **filters) -> Dict[str, Dict]:
        """Search users by filters"""
        async with self._lock:
            results = {}
            for user_id, user_data in self._memory.items():
                match = True
                for key, value in filters.items():
                    if user_data.get(key) != value:
                        match = False
                        break
                if match:
                    results[user_id] = user_data
            return results


# Global user memory instance
user_memory = UserMemory()


def get_user_memory() -> UserMemory:
    """Get global user memory instance"""
    return user_memory
