from django.contrib import admin

from inventory.models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin[InventoryItem]):
    list_display = ["product", "quantity", "unit_code", "minimum_quantity"]
    list_filter = ["product__household"]
