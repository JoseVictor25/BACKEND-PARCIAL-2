from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta
from roles.models import Rol


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    # 🔥 Relación directa con el modelo Rol
    rol = models.ForeignKey(
        Rol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios"
    )

    def __str__(self):
        return f"{self.username} ({self.rol.nombre if self.rol else 'Sin rol'})"


def default_expiration_time():
    """Devuelve la fecha de expiración del token (15 min desde ahora)."""
    return timezone.now() + timedelta(minutes=15)


class PasswordResetToken(models.Model):
    """Modelo para almacenar tokens de reseteo de contraseña."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens"
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiration_time)

    def is_valid(self):
        """Verifica si el token aún es válido."""
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Token {self.token} para {self.user.username}"
