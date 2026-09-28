_INSTRUCTIONS = (
    "Nazwy produktów pochodzą z paragonów sklepowych: mogą być w liczbie mnogiej, "
    "zawierać markę, gramaturę albo formę opakowania.\n"
    "Dopuszczaj polską odmianę i liczbę mnogą: „jajko” to to samo co „Jaja”, "
    "„mąka” to to samo co „Mąka pszenna”.\n"
    "Nie dopuszczaj produktów tylko podobnych: masło to nie maślanka, mleko to nie skyr, "
    "mąka to nie makaron, ser to nie serek.\n"
    "Jeśli żaden produkt z listy nie jest tym składnikiem, odpowiedz 0."
)


def build_matching_prompt(ingredient_name: str, product_names: tuple[str, ...]) -> str:
    listing = "\n".join(
        f"{position}. {name}" for position, name in enumerate(product_names, start=1)
    )
    return (
        f"{_INSTRUCTIONS}\n\n"
        f"Składnik przepisu: {ingredient_name}\n\n"
        f"Produkty w spiżarni:\n{listing}\n\n"
        "Odpowiedz wyłącznie jedną liczbą: numerem produktu z powyższej listy, "
        "który jest tym składnikiem, albo 0. Nie podawaj nazwy produktu."
    )
