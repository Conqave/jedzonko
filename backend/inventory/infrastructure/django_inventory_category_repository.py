from inventory.application.errors import DuplicateInventoryCategoryError
from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from inventory.domain.category import InventoryCategorySnapshot
from inventory.models import InventoryCategory


class DjangoInventoryCategoryRepository(InventoryCategoryRepository):
    def list_categories(self, household_id: int) -> list[InventoryCategorySnapshot]:
        rows = InventoryCategory.objects.filter(household_id=household_id)
        return [InventoryCategorySnapshot(id=row.pk, name=row.name) for row in rows]

    def create_category(self, household_id: int, name: str) -> InventoryCategorySnapshot:
        if InventoryCategory.objects.filter(household_id=household_id, name=name).exists():
            raise DuplicateInventoryCategoryError
        row = InventoryCategory.objects.create(household_id=household_id, name=name)
        return InventoryCategorySnapshot(id=row.pk, name=row.name)

    def find_household_id_for_category(self, category_id: int) -> int | None:
        row = (
            InventoryCategory.objects.filter(pk=category_id)
            .values_list("household_id", flat=True)
            .first()
        )
        return None if row is None else int(row)

    def rename_category(self, category_id: int, name: str) -> InventoryCategorySnapshot:
        row = InventoryCategory.objects.get(pk=category_id)
        is_taken = (
            InventoryCategory.objects.filter(household_id=row.household_id, name=name)
            .exclude(pk=category_id)
            .exists()
        )
        if is_taken:
            raise DuplicateInventoryCategoryError
        row.name = name
        row.save(update_fields=["name"])
        return InventoryCategorySnapshot(id=row.pk, name=row.name)

    def delete_category(self, category_id: int) -> None:
        InventoryCategory.objects.filter(pk=category_id).delete()
