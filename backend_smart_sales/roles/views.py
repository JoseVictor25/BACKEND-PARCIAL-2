from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from bitacora.models import Bitacora
from users.views import get_client_ip
from .models import Rol, Permiso, RolPermiso
from .serializers import RolSerializer, PermisoSerializer, RolPermisoSerializer


class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        permiso = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Creó permiso: {permiso.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )


class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        rol = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Creó rol: {rol.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )


class RolPermisoViewSet(viewsets.ModelViewSet):
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        relacion = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Asoció permiso '{relacion.permiso.nombre}' al rol '{relacion.rol.nombre}'",
            ip=get_client_ip(self.request),
            estado=True
        )
