from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel

from app.application.flow_engine import FlowEngine
from app.application.ports import ConversationRepository, SlotExtractor
from app.domain.exceptions import ConversationNotFoundError
from app.domain.models.conversation import (
    ConversationMessage,
    ConversationState,
    SectionAttempts,
    SlotValue,
)
from app.domain.models.quote import Quote


class ChatResult(BaseModel):
    session_id: str
    reply: str
    status: str
    current_section: str
    completed_sections: list[str]
    collected_slots: dict[str, SlotValue]
    missing_slots: list[str]
    attempts: dict[str, SectionAttempts]
    quote: Quote | None
    asset_ids: list[str]


class ChatService:
    """Coordinates session persistence, extraction, workflow, and response mapping."""

    def __init__(
        self,
        repository: ConversationRepository,
        extractor: SlotExtractor,
        flow_engine: FlowEngine,
    ) -> None:
        self._repository = repository
        self._extractor = extractor
        self._flow_engine = flow_engine

    def create_session(self, session_id: str | None = None) -> ConversationState:
        state = ConversationState(
            session_id=session_id or str(uuid4()),
            current_section=self._flow_engine.first_section_id,
        )
        return self._repository.create(state)

    def get_session(self, session_id: str) -> ConversationState:
        state = self._repository.get(session_id)
        if state is None:
            raise ConversationNotFoundError(f"Session '{session_id}' was not found")
        return state

    def chat(self, message: str, session_id: str | None = None) -> ChatResult:
        state = (
            self.create_session(session_id) if session_id is None else self.get_session(session_id)
        )
        state.message_history.append(ConversationMessage(role="user", content=message))
        extraction = self._extractor.extract(message)
        outcome = self._flow_engine.process(state, extraction, message)
        state.message_history.append(ConversationMessage(role="assistant", content=outcome.reply))
        state.updated_at = datetime.now(UTC)
        self._repository.save(state)
        return ChatResult(
            session_id=state.session_id,
            reply=outcome.reply,
            status=state.status.value,
            current_section=state.current_section,
            completed_sections=state.completed_sections,
            collected_slots=state.slots,
            missing_slots=outcome.missing_slots,
            attempts=state.attempts_by_section,
            quote=state.quote,
            asset_ids=outcome.asset_ids,
        )
