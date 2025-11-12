from rest_framework import serializers
from .models import Venta, DetalleVenta , Garantia
from producto.serializers import ProductoSerializer


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_detalle = ProductoSerializer(source="producto", read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id', 'producto', 'producto_detalle', 'cantidad', 'precio_unitario', 'subtotal']

class VentaSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = ['id', 'usuario', 'fecha', 'total', 'estado', 'detalles']
        read_only_fields = ['usuario', 'total', 'fecha']




class GarantiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Garantia
        fields = ['id', 'producto', 'venta', 'fecha_inicio', 'fecha_fin', 'estado']
