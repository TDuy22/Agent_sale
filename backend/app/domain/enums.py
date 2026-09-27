from enum import StrEnum


class ConversationStatus(StrEnum):
    COLLECTING = "COLLECTING"
    QUOTED = "QUOTED"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    COMPLETED = "COMPLETED"


class SectionKind(StrEnum):
    COLLECT = "collect"
    QUOTE = "quote"


class FailurePolicy(StrEnum):
    NEEDS_HUMAN = "needs_human"
    USE_DEFAULTS = "use_defaults"


class UserIntent(StrEnum):
    SHOW_SAMPLE = "show_sample"
    SHOW_COLOR = "show_color"
    SHOW_ACCESSORIES = "show_accessories"
    REQUEST_QUOTE = "request_quote"
