_INSTRUCTIONS = (
    "Nazwa produktu pochodzi ze spiżarni albo z paragonu: może zawierać markę, gramaturę "
    "albo formę opakowania. Poniżej jest pełna lista tagów składników z serwisu Ania Gotuje.\n"
    "Wybierz wszystkie tagi, które opisują ten produkt jako składnik przepisu; zwykle jest "
    "to jeden tag, czasem kilka (np. „Pesto pomidorowe” to „pesto” i „pomidory suszone”, "
    "jeśli oba są na liście). Dopuszczaj polską odmianę i liczbę mnogą: „Jaja ściółkowe "
    "(opakowanie)” to „jajka”.\n"
    "Nie wybieraj tagów tylko podobnych: maślanka to nie masło, skyr to nie mleko, "
    "makaron to nie mąka, serek to nie ser. Produkty niespożywcze nie mają tagów.\n"
    "Jeśli żaden tag nie pasuje, zwróć pustą listę."
)


def build_classification_prompt(product_name: str, tag_names: tuple[str, ...]) -> str:
    listing = "\n".join(f"{position}. {name}" for position, name in enumerate(tag_names, start=1))
    return (
        f"{_INSTRUCTIONS}\n\n"
        f"Produkt: {product_name}\n\n"
        f"Tagi:\n{listing}\n\n"
        "Odpowiedz obiektem JSON z listą „tags” zawierającą numery wybranych tagów."
    )


def build_classification_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {"tags": {"type": "array", "items": {"type": "integer"}}},
        "required": ["tags"],
    }
