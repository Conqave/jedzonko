from django.contrib import admin

from inventory.models import InventoryCategory, InventoryItem


@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin[InventoryCategory]):
    list_display = ["name", "household"]


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin[InventoryItem]):
    list_display = ["product", "quantity", "unit_code", "minimum_quantity"]
    list_filter = ["product__household"]
