from django.db import models
from producto.models import Producto


class Descuento(models.Model):
    """
    Modelo para gestionar promociones y descuentos aplicables a productos.
    """
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='descuentos',
        null=True,
        blank=True,
        help_text="Producto al que se aplica el descuento (opcional para descuentos generales)"
    )
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje de descuento (ej: 15.50 para 15.5%)"
    )
    fecha_inicio = models.DateField(help_text="Fecha de inicio de la promoción")
    fecha_fin = models.DateField(help_text="Fecha de finalización de la promoción")
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción de la promoción"
    )
    activo = models.BooleanField(default=True, help_text="Indica si el descuento está activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Descuento"
        verbose_name_plural = "Descuentos"

    def __str__(self):
        producto_nombre = self.producto.nombre if self.producto else "General"
        return f"{producto_nombre} - {self.porcentaje}% ({self.fecha_inicio} al {self.fecha_fin})"

    def esta_vigente(self):
        """Verifica si el descuento está vigente en la fecha actual."""
        from django.utils import timezone
        hoy = timezone.now().date()
        return self.activo and self.fecha_inicio <= hoy <= self.fecha_fin

    def calcular_precio_con_descuento(self, precio_original):
        """Calcula el precio con el descuento aplicado."""
        if self.esta_vigente():
            descuento_decimal = self.porcentaje / 100
            return precio_original * (1 - descuento_decimal)
        return precio_original


