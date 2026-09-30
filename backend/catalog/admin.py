from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils import timezone

from catalog.models import (
    Ingredient,
    IngredientName,
    IngredientNameCandidate,
    Product,
    ProductIngredient,
)
from config.composition import container


class IngredientNameInline(admin.TabularInline[IngredientName, Ingredient]):
    model = IngredientName
    extra = 0
    fields = ["name", "normalized_name", "kind", "source"]
    readonly_fields = ["normalized_name", "kind", "source"]

    def has_add_permission(self, request: HttpRequest, obj: Ingredient | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Ingredient | None = None) -> bool:
        return False


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin[Ingredient]):
    list_display = ["name", "kcal_per_100g", "kcal_source", "created_at"]
    list_filter = ["kcal_source"]
    search_fields = ["names__normalized_name", "name"]
    inlines = [IngredientNameInline]
    readonly_fields = ["name", "kcal_per_100g", "kcal_source", "kcal_reference_url", "created_at"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Ingredient | None = None) -> bool:
        return False


@admin.register(IngredientNameCandidate)
class IngredientNameCandidateAdmin(admin.ModelAdmin[IngredientNameCandidate]):
    list_display = ["name", "source", "status", "created_at", "decided_at"]
    list_filter = ["status", "source"]
    search_fields = ["name", "normalized_name"]
    readonly_fields = ["name", "normalized_name", "source", "status", "created_at", "decided_at"]
    actions = ["accept_as_ingredients", "dismiss"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: IngredientNameCandidate | None = None
    ) -> bool:
        return False

    @admin.action(description="Accept as new ingredients")
    def accept_as_ingredients(
        self, request: HttpRequest, queryset: QuerySet[IngredientNameCandidate]
    ) -> None:
        for candidate in queryset:
            now = timezone.now()
            use_case = container().catalog.accept_candidate_as_ingredient
            use_case.execute(candidate.pk, now)
        self.message_user(request, f"Accepted {queryset.count()} name(s).", messages.SUCCESS)

    @admin.action(description="Dismiss")
    def dismiss(self, request: HttpRequest, queryset: QuerySet[IngredientNameCandidate]) -> None:
        for candidate in queryset:
            now = timezone.now()
            use_case = container().catalog.dismiss_candidate
            use_case.execute(candidate.pk, now)
        self.message_user(request, f"Dismissed {queryset.count()} name(s).", messages.SUCCESS)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin[Product]):
    list_display = ["name", "household", "default_unit_code", "is_food"]
    list_filter = ["household", "is_food"]
    search_fields = ["name"]
    readonly_fields = ["normalized_name"]


@admin.register(ProductIngredient)
class ProductIngredientAdmin(admin.ModelAdmin[ProductIngredient]):
    list_display = ["product", "ingredient", "status", "source", "decided_at"]
    list_filter = ["status", "source"]
    search_fields = ["product__name", "ingredient__name"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: ProductIngredient | None = None
    ) -> bool:
        return False
