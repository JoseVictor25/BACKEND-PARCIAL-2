from django.db import models
from django.conf import settings


class Reporte(models.Model):
    """
    Modelo para gestionar reportes dinámicos del sistema.
    """
    TIPO_CHOICES = [
        ('ventas', 'Reporte de Ventas'),
        ('productos', 'Reporte de Productos'),
        ('clientes', 'Reporte de Clientes'),
        ('inventario', 'Reporte de Inventario'),
        ('financiero', 'Reporte Financiero'),
    ]

    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        help_text="Tipo de reporte a generar"
    )
    descripcion = models.TextField(
        help_text="Descripción del contenido del reporte"
    )
    fecha_generacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de generación del reporte"
    )
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reportes_generados',
        help_text="Usuario que generó el reporte"
    )
    formato = models.CharField(
        max_length=10,
        choices=FORMATO_CHOICES,
        default='pdf',
        help_text="Formato del reporte"
    )
    archivo = models.FileField(
        upload_to='reportes/%Y/%m/',
        null=True,
        blank=True,
        help_text="Archivo del reporte generado"
    )
    parametros = models.JSONField(
        default=dict,
        help_text="Parámetros utilizados para generar el reporte"
    )
    fecha_inicio = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de inicio del período del reporte"
    )
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de fin del período del reporte"
    )

    class Meta:
        ordering = ['-fecha_generacion']
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_generacion.strftime('%d/%m/%Y %H:%M')}"
    
    