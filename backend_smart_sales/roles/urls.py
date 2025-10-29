from rest_framework.routers import DefaultRouter
from .views import RolViewSet, PermisoViewSet, RolPermisoViewSet

router = DefaultRouter()
router.register(r"roles", RolViewSet, basename="roles")
router.register(r"permisos", PermisoViewSet, basename="permisos")
router.register(r"roles-permisos", RolPermisoViewSet, basename="roles-permisos")

urlpatterns = router.urls
