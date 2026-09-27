import unicodedata


def fold(text: str) -> str:
    """Lowercase and strip Vietnamese diacritics so matching ignores accents."""

    normalized = unicodedata.normalize("NFD", text.lower())
    folded = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return folded.replace("đ", "d")
