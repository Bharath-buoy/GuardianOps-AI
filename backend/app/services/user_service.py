"""
User Account Service
=====================
GuardianOps AI is intentionally single-user (one admin operator per
deployment) — there is no multi-tenant support. This service enforces
"only one account may ever be registered" while still persisting that
account to MongoDB when available, so it survives restarts.

Falls back to a process-local in-memory record when Mongo isn't connected,
matching the same graceful-degradation pattern used by the mock data store.
"""
import re
import uuid
from datetime import datetime, timezone

from app.core.database import get_collection
from app.core.security import hash_password, verify_password

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserService:
    def __init__(self) -> None:
        self._in_memory_user: dict | None = None

    def is_valid_email(self, email: str) -> bool:
        return bool(EMAIL_RE.match(email))

    async def user_exists(self) -> bool:
        """GuardianOps AI allows exactly one registered user."""
        collection = get_collection("users")
        if collection is not None:
            count = await collection.count_documents({})
            return count > 0
        return self._in_memory_user is not None

    async def register(self, name: str, email: str, password: str) -> dict:
        if await self.user_exists():
            raise ValueError("A GuardianOps AI account already exists. Only one operator account is supported.")
        if not self.is_valid_email(email):
            raise ValueError("Invalid email address.")

        user = {
            "user_id": f"USR-{uuid.uuid4().hex[:10].upper()}",
            "name": name,
            "email": email.lower().strip(),
            "password_hash": hash_password(password),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        collection = get_collection("users")
        if collection is not None:
            await collection.insert_one(dict(user))
        else:
            self._in_memory_user = user

        return user

    async def get_by_email(self, email: str) -> dict | None:
        collection = get_collection("users")
        email_normalized = email.lower().strip()
        if collection is not None:
            return await collection.find_one({"email": email_normalized}, {"_id": 0})
        if self._in_memory_user and self._in_memory_user["email"] == email_normalized:
            return self._in_memory_user
        return None

    async def authenticate(self, email: str, password: str) -> dict | None:
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        return user


# Singleton instance shared across the app
user_service = UserService()
