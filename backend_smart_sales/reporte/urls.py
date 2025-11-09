from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import ReporteViewSet
from . import reporte_dinamico_views  # ← NUEVA LÍNEA

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reporte')

urlpatterns = [
    # ⭐ NUEVAS RUTAS para reportes dinámicos con IA
    path(
        'reportes/generar-dinamico/',
        reporte_dinamico_views.generar_reporte_dinamico,
        name='generar-reporte-dinamico'
    ),
    path(
        'reportes/generar-por-voz/',
        reporte_dinamico_views.generar_reporte_por_voz,
        name='generar-reporte-por-voz'
    ),
    path(
        'reportes/interpretar-prompt/',
        reporte_dinamico_views.interpretar_prompt_preview,
        name='interpretar-prompt'
    ),
    
    path(
    'reportes/generar-desde-audio/',
    reporte_dinamico_views.generar_reporte_desde_audio,
    name='generar-reporte-desde-audio'
),
]

# Agregar las rutas del router AL FINAL
urlpatterns += router.urls

