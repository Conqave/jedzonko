from django.contrib import admin

from recipes.models import Recipe, RecipeCategory, RecipeTag

admin.site.register(Recipe)
admin.site.register(RecipeCategory)
admin.site.register(RecipeTag)
