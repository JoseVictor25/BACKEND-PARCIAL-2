from django.db import models
from producto.models import Producto
from users.models import CustomUser
from venta.models import Venta
# Create your models here.



class Mantenimiento(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)  # Relación con el modelo Producto
    tecnico = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'rol__nombre': 'Técnico'})  # Relación con el modelo CustomUser (solo técnicos)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='mantenimientos')  # Relación con la venta
    fecha_solicitud = models.DateTimeField(auto_now_add=True)  # Fecha en que se solicita el mantenimiento
    fecha_realizacion = models.DateTimeField(null=True, blank=True)  # Fecha en que se realiza el mantenimiento (puede estar vacía si no se ha realizado)
    tipo_mantenimiento = models.CharField(max_length=50, choices=[('preventivo', 'Preventivo'), ('correctivo', 'Correctivo')])  # Tipo de mantenimiento
    estado = models.CharField(max_length=50, choices=[('pendiente', 'Pendiente'), ('en_proceso', 'En Proceso'), ('completado', 'Completado')])  # Estado del mantenimiento
    detalles = models.TextField()  # Detalles del mantenimiento (Descripción o notas adicionales)

    def __str__(self):
        return f"{self.producto.nombre} - {self.estado}"


