from django.contrib import admin

from inventory.models import InventoryCategory, InventoryItem


@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin[InventoryCategory]):
    list_display = ["name", "household"]


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin[InventoryItem]):
    list_display = ["ingredient", "household", "quantity", "unit", "minimum_quantity"]
    list_filter = ["household"]
