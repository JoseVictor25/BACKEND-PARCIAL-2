from django.urls import path
from .views import LoginView, LogoutView, RegisterView, PasswordResetRequestView, PasswordResetConfirmView, AsignarRolView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("password-reset-request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("asignar-rol/", AsignarRolView.as_view(), name="asignar-rol"),
]
