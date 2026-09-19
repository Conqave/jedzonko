import unicodedata

# NFKD leaves "ł"/"Ł" undecomposed, so they need an explicit mapping.
_LATIN_STROKE_TRANSLATION = str.maketrans({"ł": "l", "Ł": "l"})


def normalize_text(text: str) -> str:
    folded = text.casefold().translate(_LATIN_STROKE_TRANSLATION)
    decomposed = unicodedata.normalize("NFKD", folded)
    stripped = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(stripped.split())
