from rest_framework import viewsets,filters
from rest_framework.permissions import AllowAny
from bitacora.models import Bitacora
from users.views import get_client_ip
from .models import Producto
from .serializers import ProductoSerializer
from django_filters.rest_framework import DjangoFilterBackend


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]




 # 🧩 Agregamos filtros, búsqueda y ordenamiento
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filtros exactos
    filterset_fields = ['marca', 'categoria', 'estado']

    # Campos donde se puede hacer búsqueda parcial
    search_fields = ['nombre', 'descripcion', 'marca__nombre', 'categoria__nombre']

    # Campos que se pueden usar para ordenar
    ordering_fields = ['precio', 'fecha_creacion', 'nombre']





    def perform_create(self, serializer):
        producto = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Creó producto: {producto.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_update(self, serializer):
        producto = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Actualizó producto: {producto.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_destroy(self, instance):
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Eliminó producto: {instance.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )
        instance.delete()
