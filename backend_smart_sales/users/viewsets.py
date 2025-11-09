<<<<<<< HEAD
from bitacora.models import Bitacora
from users.views import get_client_ip

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import CustomUser
from .serializers import UserSerializer
from roles.models import Rol
=======
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import CustomUser
from .serializers import UserSerializer
from bitacora.models import Bitacora
from users.views import get_client_ip
>>>>>>> main

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
<<<<<<< HEAD
    permission_classes = [AllowAny]  # Solo admins pueden listar/editar usuarios

    def create(self, request, *args, **kwargs):
        print("📦 Datos recibidos:", request.data)  # 👈 agrega esto
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
=======
    permission_classes = [IsAuthenticated]  # Solo admins pueden listar/editar usuarios

    def perform_create(self, serializer):
>>>>>>> main
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
