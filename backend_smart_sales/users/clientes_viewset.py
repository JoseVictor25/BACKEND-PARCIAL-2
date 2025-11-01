from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from users.models import CustomUser
from users.serializers import UserSerializer
from bitacora.models import Bitacora
from users.views import get_client_ip
from roles.models import Rol

class ClienteViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomUser.objects.filter(rol__nombre__iexact="Cliente")

    def perform_create(self, serializer):
        cliente = serializer.save()
        rol_cliente = Rol.objects.filter(nombre__iexact="Cliente").first()
        if rol_cliente:
            cliente.rol = rol_cliente
            cliente.save()

        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Creó cliente: {cliente.username}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_update(self, serializer):
        cliente = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Actualizó cliente: {cliente.username}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_destroy(self, instance):
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Eliminó cliente: {instance.username}",
            ip=get_client_ip(self.request),
            estado=True
        )
        instance.delete()
