from dataclasses import dataclass, field

from app.application.quotation_service import QuotationService
from app.application.response_service import ResponseService
from app.application.slot_service import SlotService
from app.domain.enums import ConversationStatus, FailurePolicy
from app.domain.models.conversation import (
    ConversationState,
    SectionAttempts,
    SlotExtractionResult,
)
from app.domain.models.flow import FlowDefinition


@dataclass(slots=True)
class EngineResult:
    reply: str
    missing_slots: list[str] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)


class FlowEngine:
    """Configuration-driven finite-state workflow for one user message."""

    def __init__(
        self,
        flow: FlowDefinition,
        slot_service: SlotService,
        quotation_service: QuotationService,
        response_service: ResponseService,
    ) -> None:
        self._flow = flow
        self._slots = slot_service
        self._quotes = quotation_service
        self._responses = response_service

    @property
    def first_section_id(self) -> str:
        return self._flow.sections[0].id

    def process(
        self,
        state: ConversationState,
        extraction: SlotExtractionResult,
        source_message: str,
    ) -> EngineResult:
        accepted, changed_any = self._slots.merge(state, extraction, source_message)
        if changed_any and state.quote is not None:
            state.quote = None
            state.status = ConversationStatus.COLLECTING

        if state.status == ConversationStatus.NEEDS_HUMAN and accepted:
            state.status = ConversationStatus.COLLECTING

        while True:
            section = self._flow.section(state.current_section)

            if section.id == "quotation":
                if state.quote is None:
                    state.status = ConversationStatus.READY_TO_QUOTE
                    next_version = state.quote_version + 1
                    state.quote = self._quotes.create_quote(state, next_version)
                    state.quote_version = next_version
                state.status = ConversationStatus.QUOTED
                if section.id not in state.completed_sections:
                    state.completed_sections.append(section.id)
                state.last_asked_fields = []
                state.last_asked_section = None
                return EngineResult(
                    reply=self._responses.quote_ready(state.quote),
                    asset_ids=self._responses.assets_for(state),
                )

            if section.failure_policy == FailurePolicy.USE_DEFAULTS:
                self._slots.apply_defaults(state, section.defaults, section.id)

            missing = self._slots.missing_or_invalid(state, section.required_slots)
            if missing:
                attempts = state.attempts_by_section.setdefault(section.id, SectionAttempts())
                attempts.turn_count += 1
                was_answering_this_section = state.last_asked_section == section.id
                answered_asked_field = bool(accepted.intersection(state.last_asked_fields))
                if (
                    was_answering_this_section
                    and state.last_asked_fields
                    and not answered_asked_field
                ):
                    attempts.failed_attempt_count += 1

                if attempts.failed_attempt_count >= section.max_attempts:
                    if section.failure_policy == FailurePolicy.USE_DEFAULTS:
                        self._slots.apply_defaults(state, section.defaults, section.id)
                        missing = self._slots.missing_or_invalid(state, section.required_slots)
                    if missing:
                        state.status = ConversationStatus.NEEDS_HUMAN
                        return EngineResult(
                            reply=self._responses.needs_human(missing),
                            missing_slots=missing,
                        )

                state.status = ConversationStatus.COLLECTING
                state.last_asked_fields = missing
                state.last_asked_section = section.id
                return EngineResult(reply=self._responses.ask_for(missing), missing_slots=missing)

            if section.id not in state.completed_sections:
                state.completed_sections.append(section.id)
            state.last_asked_fields = []
            state.last_asked_section = None
            current_index = self._flow.index_of(section.id)
            if current_index + 1 >= len(self._flow.sections):
                state.status = ConversationStatus.COMPLETED
                return EngineResult(reply="Phiên tư vấn đã hoàn tất.")
            state.current_section = self._flow.sections[current_index + 1].id
