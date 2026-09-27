from dataclasses import dataclass, field

from app.application.image_asset_skill import ImageAssetSkill
from app.application.quotation_service import QuotationService
from app.application.response_service import ResponseService
from app.application.slot_service import SlotService
from app.domain.enums import ConversationStatus, FailurePolicy, SectionKind
from app.domain.models.asset import Asset
from app.domain.models.conversation import (
    ConversationState,
    SectionAttempts,
    SlotExtractionResult,
)
from app.domain.models.flow import FlowDefinition, FlowSection


@dataclass(slots=True)
class EngineResult:
    reply: str
    missing_slots: list[str] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)


class FlowEngine:
    """Configuration-driven finite-state workflow for one user message.

    Each turn: merge extracted slots into memory, then walk sections from the current one.
    A complete section advances the flow; an incomplete one asks for the missing slots,
    and after too many failed answers falls back to defaults or a human consultant.
    """

    def __init__(
        self,
        flow: FlowDefinition,
        slot_service: SlotService,
        quotation_service: QuotationService,
        response_service: ResponseService,
        asset_skill: ImageAssetSkill,
    ) -> None:
        self._flow = flow
        self._slots = slot_service
        self._quotes = quotation_service
        self._responses = response_service
        self._asset_skill = asset_skill

    @property
    def first_section_id(self) -> str:
        return self._flow.sections[0].id

    @property
    def greeting(self) -> str:
        return self._flow.greeting

    def process(
        self,
        state: ConversationState,
        extraction: SlotExtractionResult,
        source_message: str,
    ) -> EngineResult:
        accepted, changed = self._slots.merge(state, extraction, source_message)
        state.last_intents = extraction.intents
        if changed and state.quote is not None:
            state.quote = None
            state.status = ConversationStatus.COLLECTING
        if accepted and state.status == ConversationStatus.NEEDS_HUMAN:
            state.status = ConversationStatus.COLLECTING

        suggested_asset_ids: list[str] = []
        while True:
            section = self._flow.section(state.current_section)

            if section.kind == SectionKind.QUOTE:
                reply = self._quote(state, section)
                return self._result(state, reply, source_message, extraction, suggested_asset_ids)

            missing = self._slots.missing_or_invalid(state, section.required_slots)
            if missing and self._attempts_exhausted(state, section, accepted):
                if section.failure_policy == FailurePolicy.USE_DEFAULTS:
                    self._slots.apply_defaults(state, section.defaults, section.id)
                    missing = self._slots.missing_or_invalid(state, section.required_slots)
                if missing:
                    state.status = ConversationStatus.NEEDS_HUMAN
                    reply = self._responses.needs_human(missing)
                    return self._result(
                        state, reply, source_message, extraction, suggested_asset_ids, missing
                    )
            if missing:
                state.status = ConversationStatus.COLLECTING
                state.last_asked_fields = missing
                state.last_asked_section = section.id
                reply = self._responses.ask_for(missing)
                return self._result(
                    state, reply, source_message, extraction, suggested_asset_ids, missing
                )

            if section.id not in state.completed_sections:
                state.completed_sections.append(section.id)
                suggested_asset_ids.extend(section.suggested_assets)
            self._clear_question(state)

            next_section = self._flow.next_section(section.id)
            if next_section is None:
                state.status = ConversationStatus.COMPLETED
                reply = self._responses.completed()
                return self._result(state, reply, source_message, extraction, suggested_asset_ids)
            state.current_section = next_section.id

    def _quote(self, state: ConversationState, section: FlowSection) -> str:
        if state.quote is None:
            state.quote_version += 1
            state.quote = self._quotes.create_quote(state, state.quote_version)
        state.status = ConversationStatus.QUOTED
        if section.id not in state.completed_sections:
            state.completed_sections.append(section.id)
        self._clear_question(state)
        return self._responses.quote_ready(state.quote)

    @staticmethod
    def _attempts_exhausted(
        state: ConversationState, section: FlowSection, accepted: set[str]
    ) -> bool:
        attempts = state.attempts_by_section.setdefault(section.id, SectionAttempts())
        attempts.turn_count += 1
        # Only count a failure when the user was answering this exact question.
        if (
            state.last_asked_section == section.id
            and state.last_asked_fields
            and not accepted.intersection(state.last_asked_fields)
        ):
            attempts.failed_attempt_count += 1
        return attempts.failed_attempt_count >= section.max_attempts

    @staticmethod
    def _clear_question(state: ConversationState) -> None:
        state.last_asked_fields = []
        state.last_asked_section = None

    def _result(
        self,
        state: ConversationState,
        reply: str,
        source_message: str,
        extraction: SlotExtractionResult,
        suggested_asset_ids: list[str],
        missing_slots: list[str] | None = None,
    ) -> EngineResult:
        assets = self._asset_skill.select_assets(
            state, source_message, extraction.intents, suggested_asset_ids
        )
        return EngineResult(
            reply=self._responses.with_assets(reply, assets),
            missing_slots=missing_slots or [],
            assets=assets,
        )
