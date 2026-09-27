from enum import StrEnum


class ConversationStatus(StrEnum):
    COLLECTING = "COLLECTING"
    READY_TO_QUOTE = "READY_TO_QUOTE"
    QUOTED = "QUOTED"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    COMPLETED = "COMPLETED"


class FailurePolicy(StrEnum):
    NEEDS_HUMAN = "needs_human"
    USE_DEFAULTS = "use_defaults"


class QuoteStatus(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    INCOMPLETE = "INCOMPLETE"


class UserIntent(StrEnum):
    SHOW_SAMPLE = "show_sample"
    SHOW_COLOR = "show_color"
    SHOW_ACCESSORIES = "show_accessories"
    REQUEST_QUOTE = "request_quote"
