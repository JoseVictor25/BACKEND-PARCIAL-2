from rest_framework import serializers
from .models import Bitacora

class BitacoraSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()

    class Meta:
        model = Bitacora
        fields = ['id', 'usuario', 'accion', 'ip', 'fecha_hora', 'estado']
