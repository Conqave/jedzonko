def matches_name(
    normalized_name: str, candidate_normalized_name: str, tag_names: tuple[str, ...]
) -> bool:
    if normalized_name in tag_names:
        return True
    required_words = normalized_name.split()
    if not required_words:
        return False
    candidate_words = set(candidate_normalized_name.split())
    return all(word in candidate_words for word in required_words)
