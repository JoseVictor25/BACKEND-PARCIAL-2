from django.db import models
from django.conf import settings
from producto.models import Producto
from datetime import datetime
from dateutil.relativedelta import relativedelta  # Correcta importación de relativedelta


class Venta(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('cancelado', 'Cancelado'),
        ('entregado', 'Entregado'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    def __str__(self):
        return f"Venta #{self.id} - {self.usuario.username}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"




class Garantia(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name='garantia_producto')
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='garantia_venta')
    fecha_inicio =models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=50, choices=[('activa', 'Activa'), ('caducada', 'Caducada')])

    def save(self, *args, **kwargs):
        # La fecha de inicio es la fecha de la venta

        # Calculamos la fecha de fin sumando los meses de la garantía al inicio
        self.fecha_fin = self.fecha_inicio + relativedelta(months=self.producto.garantia)

        # Verificar si la garantía ha caducado
        if self.fecha_fin < datetime.now().date():
            self.estado = 'caducada'  # Cambiar el estado a "caducada" si la fecha de fin ha pasado
        else:
            self.estado = 'activa'  # Si no ha caducado, aseguramos que el estado sea "activa"
        
        # Llamamos al save original para guardar los cambios
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Garantía de {self.producto.nombre} - {self.estado}"