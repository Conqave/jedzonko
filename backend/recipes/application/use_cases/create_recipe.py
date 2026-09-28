from recipes.application.commands import RecipeInput
from recipes.application.ingredients import resolve_recipe_ingredients
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.models import RecipeDetail
from shared.transactions import TransactionManager


class CreateRecipe:
    def __init__(
        self,
        repository: RecipeRepository,
        resolver: IngredientResolver,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._resolver = resolver
        self._transactions = transactions

    def execute(self, user_id: int, command: RecipeInput) -> RecipeDetail:
        ingredients = resolve_recipe_ingredients(command.ingredients, self._resolver)
        with self._transactions.atomic():
            return self._repository.create_recipe(command, ingredients, user_id)
