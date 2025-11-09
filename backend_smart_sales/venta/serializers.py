from rest_framework import serializers
from .models import Venta, DetalleVenta
from producto.serializers import ProductoSerializer


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_detalle = ProductoSerializer(source="producto", read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id', 'producto', 'producto_detalle', 'cantidad', 'precio_unitario', 'subtotal']

<<<<<<< HEAD
=======

>>>>>>> main
class VentaSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = ['id', 'usuario', 'fecha', 'total', 'estado', 'detalles']
<<<<<<< HEAD
        read_only_fields = ['usuario', 'total', 'fecha']
=======
        read_only_fields = ['usuario', 'total', 'estado']
>>>>>>> main
