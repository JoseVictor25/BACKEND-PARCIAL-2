from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Bitacora
from .serializers import BitacoraSerializer

class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Permite listar y consultar registros de la bitácora.
    Solo usuarios autenticados pueden acceder.
    """
    queryset = Bitacora.objects.all().order_by("-fecha_hora")
    serializer_class = BitacoraSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["usuario__username", "accion", "ip"]
    ordering_fields = ["fecha_hora"]
