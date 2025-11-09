from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="SmartSales365 API",
        default_version="v1",
        description="API REST para la gestión comercial e inteligencia artificial",
        contact=openapi.Contact(email="jose@example.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),

    # Bitácora
    path("api/bitacora/", include("bitacora.urls")),

    # Roles y permisos
    path("api/", include("roles.urls")),

    # Marca
    path("api/", include("marca.urls")),

    # Categoría
    path("api/categorias/", include("categoria.urls")),

    # Producto
    path("api/", include("producto.urls")),

    # Usuarios
    path("api/", include("users.urls")),

    # Carrito
    path("api/", include("carrito.urls")),

    # Venta
    path("api/", include("venta.urls")),

    # Descuento
    path("api/", include("descuento.urls")),

    # Reporte
    path("api/", include("reporte.urls")),

    # Swagger
    path(
        "swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"
    ),
]
