from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from bitacora.models import Bitacora
from users.views import get_client_ip
from .models import Categoria
from .serializers import CategoriaSerializer

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        categoria = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Creó categoría: {categoria.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_update(self, serializer):
        categoria = serializer.save()
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Actualizó categoría: {categoria.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_destroy(self, instance):
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Eliminó categoría: {instance.nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )
        instance.delete()
