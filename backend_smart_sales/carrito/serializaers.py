from rest_framework import serializers
from .models import Carrito, DetalleCarrito
from producto.serializers import ProductoSerializer


class DetalleCarritoSerializer(serializers.ModelSerializer):
    producto_detalle = ProductoSerializer(source="producto", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = DetalleCarrito
        fields = ['id', 'producto', 'producto_detalle', 'cantidad', 'subtotal']

    def get_subtotal(self, obj):
        return obj.subtotal()


class CarritoSerializer(serializers.ModelSerializer):
    detalles = DetalleCarritoSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Carrito
        fields = ['id', 'usuario', 'fecha_creacion', 'activo', 'detalles', 'total']
        read_only_fields = ['usuario']

    def get_total(self, obj):
        return obj.total()
