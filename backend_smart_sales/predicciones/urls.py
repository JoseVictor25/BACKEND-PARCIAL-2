from django.urls import path
from .views import VentasHistoricas, PrediccionesVentas, VentasHistoricoYPredicciones

urlpatterns = [
    # Ventas históricas por mes
    path('ventas-historicas/', VentasHistoricas.as_view(), name='ventas-historicas'),

    # Predicciones para los próximos meses (solo predicciones)
    path('predicciones-ventas/', PrediccionesVentas.as_view(), name='predicciones-ventas'),

    # Histórico + predicciones combinadas
    path('ventas-historico-predicciones/', VentasHistoricoYPredicciones.as_view(), name='ventas-historico-predicciones'),
]
