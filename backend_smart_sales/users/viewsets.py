from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import CustomUser
from .serializers import UserSerializer
from bitacora.models import Bitacora
from users.views import get_client_ip

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Solo admins pueden listar/editar usuarios

    def perform_create(self, serializer):
        user = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Creó usuario: {user.username}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_update(self, serializer):
        user = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Actualizó usuario: {user.username}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_destroy(self, instance):
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Eliminó usuario: {instance.username}",
            ip=get_client_ip(self.request),
            estado=True
        )
        instance.delete()
