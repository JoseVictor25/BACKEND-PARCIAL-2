from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from bitacora.models import Bitacora
from users.views import get_client_ip
from .models import Marca
from .serializers import MarcaSerializer

class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        marca = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Creó marca: {marca.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_update(self, serializer):
        marca = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Actualizó marca: {marca.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_destroy(self, instance):
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Eliminó marca: {instance.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )
        instance.delete()
