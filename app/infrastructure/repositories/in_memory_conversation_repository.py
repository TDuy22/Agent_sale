from copy import deepcopy
from threading import RLock

from app.domain.models.conversation import ConversationState


class InMemoryConversationRepository:
    """Thread-safe process-local session store for development and tests."""

    def __init__(self) -> None:
        self._states: dict[str, ConversationState] = {}
        self._lock = RLock()

    def create(self, state: ConversationState) -> ConversationState:
        with self._lock:
            self._states[state.session_id] = deepcopy(state)
            return deepcopy(state)

    def get(self, session_id: str) -> ConversationState | None:
        with self._lock:
            state = self._states.get(session_id)
            return deepcopy(state) if state else None

    def save(self, state: ConversationState) -> ConversationState:
        with self._lock:
            self._states[state.session_id] = deepcopy(state)
            return deepcopy(state)
