from django.db import models
from django.conf import settings
from django.utils import timezone

class Bitacora(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bitacoras'
    )
    accion = models.CharField(max_length=255)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha_hora = models.DateTimeField(default=timezone.now)
    estado = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.usuario.username} - {self.accion} ({self.fecha_hora.strftime('%d/%m/%Y %H:%M:%S')})"
