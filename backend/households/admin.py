from django.contrib import admin

from households.models import Household, HouseholdMembership


class HouseholdMembershipInline(admin.TabularInline[HouseholdMembership, Household]):
    model = HouseholdMembership
    extra = 0


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin[Household]):
    list_display = ["name", "created_at", "deleted_at"]
    inlines = [HouseholdMembershipInline]
