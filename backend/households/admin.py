from django.contrib import admin

from households.models import Household, HouseholdMembership, Product


class HouseholdMembershipInline(admin.TabularInline[HouseholdMembership, Household]):
    model = HouseholdMembership
    extra = 0


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin[Household]):
    list_display = ["name", "created_at", "deleted_at"]
    inlines = [HouseholdMembershipInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin[Product]):
    list_display = ["name", "household", "default_unit_code", "is_food"]
    list_filter = ["household", "is_food"]
    search_fields = ["name"]
