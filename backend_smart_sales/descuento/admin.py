from django.contrib import admin
from .models import Descuento


@admin.register(Descuento)
class DescuentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'producto', 'porcentaje', 'fecha_inicio', 'fecha_fin', 'activo', 'esta_vigente']
    list_filter = ['activo', 'fecha_inicio', 'fecha_fin']
    search_fields = ['producto__nombre', 'descripcion']
    date_hierarchy = 'fecha_inicio'
    
    def esta_vigente(self, obj):
        return obj.esta_vigente()
    esta_vigente.boolean = True
    esta_vigente.short_description = 'Vigente'