from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.requirement_name import RecipeRequirementName


class ListRecipeRequirementNames:
    def __init__(self, repository: RecipeRepository) -> None:
        self._repository = repository

    def execute(self) -> list[RecipeRequirementName]:
        names: dict[str, str] = {}
        for requirements in self._repository.list_requirements_by_recipe().values():
            for requirement in requirements:
                names.setdefault(requirement.normalized_name, requirement.name)
        return [
            RecipeRequirementName(name=name, normalized_name=normalized)
            for normalized, name in sorted(names.items())
        ]
