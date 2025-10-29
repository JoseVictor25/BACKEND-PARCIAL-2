from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from bitacora.models import Bitacora
from users.views import get_client_ip
from .models import Producto
from .serializers import ProductoSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]

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
