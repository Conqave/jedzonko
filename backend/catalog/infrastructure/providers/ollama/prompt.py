_INSTRUCTIONS = (
    "Nazwa produktu pochodzi ze spiżarni albo z paragonu: może zawierać markę, gramaturę "
    "albo formę opakowania.\n"
    "Wybierz składnik, którym ten produkt jest. Dopuszczaj polską odmianę i liczbę mnogą: "
    "„Jaja ściółkowe (opakowanie)” to „jajka”.\n"
    "Nie wybieraj składników tylko podobnych: maślanka to nie masło, skyr to nie mleko, "
    "makaron to nie mąka, serek to nie ser.\n"
    "Jeśli żaden składnik z listy nie pasuje, odpowiedz 0."
)


def build_classification_prompt(product_name: str, ingredient_names: tuple[str, ...]) -> str:
    listing = "\n".join(
        f"{position}. {name}" for position, name in enumerate(ingredient_names, start=1)
    )
    return (
        f"{_INSTRUCTIONS}\n\n"
        f"Produkt: {product_name}\n\n"
        f"Składniki:\n{listing}\n\n"
        "Odpowiedz wyłącznie jedną liczbą: numerem składnika z powyższej listy albo 0. "
        "Nie podawaj nazwy składnika."
    )
