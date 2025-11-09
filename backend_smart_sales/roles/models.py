from django.db import models


class Permiso(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Rol(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    permisos = models.ManyToManyField("Permiso", through="RolPermiso", related_name="roles")

    def __str__(self):
        return self.nombre


class RolPermiso(models.Model):
    rol = models.ForeignKey("Rol", on_delete=models.CASCADE)
    permiso = models.ForeignKey("Permiso", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("rol", "permiso")

    def __str__(self):
        return f"{self.rol.nombre} - {self.permiso.nombre}"