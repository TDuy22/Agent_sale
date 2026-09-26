class DomainError(Exception):
    """Base exception for expected business failures."""


class ConversationNotFoundError(DomainError):
    """Raised when a requested session does not exist."""


class ConfigurationError(DomainError):
    """Raised when a YAML configuration is invalid."""


class QuoteValidationError(DomainError):
    """Raised when required quotation input is absent or invalid."""
