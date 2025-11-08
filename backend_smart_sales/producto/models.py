from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    marca = models.ForeignKey(
        "marca.Marca", on_delete=models.CASCADE, related_name="productos"
    )
    categoria = models.ForeignKey(
        "categoria.Categoria", on_delete=models.CASCADE, related_name="productos"
    )
    imagen = models.URLField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
