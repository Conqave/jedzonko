from rest_framework.exceptions import NotFound, ValidationError

from config.api_errors import ApiErrors
from inventory.application.errors import (
    DuplicateInventoryCategoryError,
    DuplicateInventoryItemError,
    DuplicateProductNameError,
    InvalidProductNameError,
    InventoryCategoryNotFoundError,
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
    InventoryCategoryNotFoundError: (
        ValidationError,
        "Unknown inventory category.",
        "inventory_category_not_found",
    ),
    DuplicateInventoryCategoryError: (
        ValidationError,
        "This category already exists in the household.",
        "duplicate_inventory_category",
    ),
    ProductNotFoundError: (ValidationError, "Unknown product.", "product_not_found"),
    MeasurementUnitNotFoundError: (
        ValidationError,
        "Unknown measurement unit.",
        "measurement_unit_not_found",
    ),
    DuplicateProductNameError: (
        ValidationError,
        "This product already exists in the household.",
        "duplicate_product",
    ),
    InvalidProductNameError: (ValidationError, "The name is empty or too long.", "invalid_name"),
    InventoryPhotoNotFoundError: (
        NotFound,
        "The inventory item has no photo.",
        "inventory_photo_not_found",
    ),
}
