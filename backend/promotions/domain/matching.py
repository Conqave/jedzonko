import unicodedata

# NFKD leaves "ł"/"Ł" undecomposed, so they need an explicit mapping.
_LATIN_STROKE_TRANSLATION = str.maketrans({"ł": "l", "Ł": "l"})


def normalize_text(text: str) -> str:
    folded = text.casefold().translate(_LATIN_STROKE_TRANSLATION)
    decomposed = unicodedata.normalize("NFKD", folded)
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def matches_query(product_name: str, query: str) -> bool:
    tokens = normalize_text(query).split()
    if not tokens:
        return False
    words = normalize_text(product_name).split()
    return all(any(word.startswith(token) for word in words) for token in tokens)
