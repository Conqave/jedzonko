from households.domain.ingredient_requirement import IngredientRequirement
from households.domain.product_names import ProductNames
from shared.name_matching import matches_name


def find_unmatched_requirements(
    requirements: list[IngredientRequirement], products: list[ProductNames]
) -> list[IngredientRequirement]:
    return [
        requirement
        for requirement in requirements
        if not any(
            matches_name(requirement.normalized_name, product.normalized_name, product.tag_names)
            for product in products
        )
    ]
