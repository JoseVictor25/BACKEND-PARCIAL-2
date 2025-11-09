from rest_framework import serializers
from .models import Producto


class ProductoSerializer(serializers.ModelSerializer):
    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True)
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id",
            "nombre",
            "descripcion",
            "precio",
            "stock",
            "marca",
            "marca_nombre",
            "categoria",
            "categoria_nombre",
            "imagen",
            "estado",
            "fecha_creacion",
        ]
