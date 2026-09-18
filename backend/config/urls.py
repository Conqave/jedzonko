from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.presentation.urls")),
    path("api/catalog/", include("catalog.presentation.urls")),
    path("api/households/", include("households.presentation.urls")),
    path("api/inventory/", include("inventory.presentation.urls")),
    path("api/promotions/", include("promotions.presentation.urls")),
    path("api/recipes/", include("recipes.presentation.urls")),
    path("api/shopping/", include("shopping.presentation.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
