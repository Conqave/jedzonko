from shared.text import normalize_text


def matches_query(product_name: str, product_brand_name: str | None, query: str) -> bool:
    tokens = normalize_text(query).split()
    if not tokens:
        return False
    words = _matchable_words(product_name, product_brand_name)
    return all(any(word.startswith(token) for word in words) for token in tokens)


def _matchable_words(product_name: str, product_brand_name: str | None) -> list[str]:
    words = normalize_text(product_name).split()
    if product_brand_name is None:
        return words
    brand_words = set(normalize_text(product_brand_name).split())
    return [word for word in words if word not in brand_words]
