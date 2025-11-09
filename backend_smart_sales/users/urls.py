from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, LogoutView, RegisterView,
    PasswordResetRequestView, PasswordResetConfirmView, AsignarRolView
)
from .viewsets import UsuarioViewSet
from .clientes_viewset import ClienteViewSet

# 🔹 1. Crear router y registrar ViewSets con prefijos distintos
router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuarios")
router.register(r"clientes", ClienteViewSet, basename="clientes")

# 🔹 2. Definir urlpatterns combinando router + vistas personalizadas
urlpatterns = [
    # Endpoints de autenticación y roles
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("password-reset-request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("asignar-rol/", AsignarRolView.as_view(), name="asignar-rol"),

    # Endpoints de usuarios y clientes
    path("", include(router.urls)),
]
