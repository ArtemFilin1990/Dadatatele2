from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserSession:
    current_inn: str = ""
    current_card: str = ""
    stack: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    expires_at: float = 0.0


class SessionStore:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[int, UserSession] = {}

    def get(self, user_id: int) -> UserSession:
        now = time.time()
        session = self._sessions.get(user_id)
        if session and session.expires_at > now:
            return session
        session = UserSession(expires_at=now + self.ttl_seconds)
        self._sessions[user_id] = session
        return session

    def save(self, user_id: int, session: UserSession) -> None:
        session.expires_at = time.time() + self.ttl_seconds
        self._sessions[user_id] = session
