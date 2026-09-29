from rest_framework.exceptions import NotFound, ValidationError

from config.api_errors import ApiErrors
from inventory.application.errors import (
    DuplicateInventoryItemError,
    InventoryItemNotFoundError,
    InventoryPhotoNotFoundError,
    MeasurementUnitNotFoundError,
    ProductNotFoundError,
)

API_ERRORS: ApiErrors = {
    InventoryItemNotFoundError: (NotFound, "Inventory item not found.", "inventory_item_not_found"),
    DuplicateInventoryItemError: (
        ValidationError,
        "This product is already in the inventory.",
        "duplicate_inventory_item",
    ),
    ProductNotFoundError: (ValidationError, "Unknown product.", "product_not_found"),
    MeasurementUnitNotFoundError: (
        ValidationError,
        "Unknown measurement unit.",
        "measurement_unit_not_found",
    ),
    InventoryPhotoNotFoundError: (
        NotFound,
        "The inventory item has no photo.",
        "inventory_photo_not_found",
    ),
}
