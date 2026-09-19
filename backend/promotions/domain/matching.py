from shared.text import normalize_text


def matches_query(product_name: str, query: str) -> bool:
    tokens = normalize_text(query).split()
    if not tokens:
        return False
    words = normalize_text(product_name).split()
    return all(any(word.startswith(token) for word in words) for token in tokens)
