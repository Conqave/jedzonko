from django.contrib import admin

from recipes.models import ExternalRecipe, Recipe, RecipeCategory, RecipeTag

admin.site.register(Recipe)
admin.site.register(RecipeCategory)
admin.site.register(RecipeTag)
admin.site.register(ExternalRecipe)
