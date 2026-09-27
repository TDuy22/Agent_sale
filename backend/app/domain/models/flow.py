from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import FailurePolicy, SectionKind


class FlowSection(BaseModel):
    """One configurable section in the conversation workflow."""

    id: str
    title: str
    goal: str
    kind: SectionKind = SectionKind.COLLECT
    required_slots: list[str] = Field(default_factory=list)
    optional_slots: list[str] = Field(default_factory=list)
    suggested_assets: list[str] = Field(default_factory=list)
    defaults: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1)
    failure_policy: FailurePolicy = FailurePolicy.NEEDS_HUMAN


class FlowDefinition(BaseModel):
    greeting: str
    slot_labels: dict[str, str] = Field(default_factory=dict)
    sections: list[FlowSection] = Field(min_length=1)

    @model_validator(mode="after")
    def section_ids_are_unique(self) -> "FlowDefinition":
        ids = [section.id for section in self.sections]
        if len(ids) != len(set(ids)):
            raise ValueError("Flow section ids must be unique")
        return self

    def section(self, section_id: str) -> FlowSection:
        return next(section for section in self.sections if section.id == section_id)

    def next_section(self, section_id: str) -> FlowSection | None:
        index = [section.id for section in self.sections].index(section_id) + 1
        return self.sections[index] if index < len(self.sections) else None
