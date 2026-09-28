from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)


class GetConfirmedProductIngredients:
    def __init__(self, repository: ProductClassificationRepository) -> None:
        self._repository = repository

    def execute(self, household_id: int) -> dict[int, int]:
        return self._repository.list_confirmed(household_id)
