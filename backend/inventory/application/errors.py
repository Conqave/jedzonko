class InventoryItemNotFoundError(Exception):
    pass


class DuplicateInventoryItemError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class MeasurementUnitNotFoundError(Exception):
    pass


class InventoryCategoryNotFoundError(Exception):
    pass


class DuplicateInventoryCategoryError(Exception):
    pass


class InventoryPhotoNotFoundError(Exception):
    pass


class DuplicateProductNameError(Exception):
    pass


class InvalidProductNameError(Exception):
    pass
