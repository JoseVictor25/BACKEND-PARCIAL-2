from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from bitacora.models import Bitacora
from users.views import get_client_ip
from .models import Carrito, DetalleCarrito
from producto.models import Producto
from .serializaers import CarritoSerializer, DetalleCarritoSerializer
from rest_framework.decorators import action

class CarritoViewSet(viewsets.ModelViewSet):
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Retorna solo el carrito del usuario autenticado
        return Carrito.objects.filter(usuario=self.request.user, activo=True)

    def perform_create(self, serializer):
        carrito = serializer.save(usuario=self.request.user)
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Creó carrito de compras",
            ip=get_client_ip(self.request),
            estado=True
        )

    # 🧩 Acción personalizada para agregar producto
    def create(self, request, *args, **kwargs):
        producto_id = request.data.get("producto_id")
        cantidad = int(request.data.get("cantidad", 1))

        producto = Producto.objects.get(id=producto_id)

        # Buscar o crear carrito activo
        carrito, created = Carrito.objects.get_or_create(usuario=request.user, activo=True)

        # Buscar si el producto ya está en el carrito
        detalle, creado = DetalleCarrito.objects.get_or_create(
            carrito=carrito, producto=producto
        )
        if not creado:
            detalle.cantidad += cantidad
        else:
            detalle.cantidad = cantidad
        detalle.save()

        Bitacora.objects.create(
            usuario=request.user,
            accion=f"Agregó {cantidad} unidad(es) de {producto.nombre} al carrito",
            ip=get_client_ip(request),
            estado=True
        )

        return Response(CarritoSerializer(carrito).data, status=status.HTTP_200_OK)

    # 🧹 Acción para vaciar carrito
    def destroy(self, request, *args, **kwargs):
        carrito = Carrito.objects.filter(usuario=request.user, activo=True).first()
        if carrito:
            carrito.detalles.all().delete()
            Bitacora.objects.create(
                usuario=request.user,
                accion="Vació su carrito de compras",
                ip=get_client_ip(request),
                estado=True
            )
            return Response({"message": "Carrito vaciado correctamente"}, status=status.HTTP_200_OK)
        return Response({"error": "No hay carrito activo"}, status=status.HTTP_404_NOT_FOUND)





 # 🧹 NUEVO: acción personalizada para vaciar el carrito
    @action(detail=False, methods=['delete'], url_path='vaciar')
    def vaciar_carrito(self, request):
        carrito = Carrito.objects.filter(usuario=request.user, activo=True).first()
        if carrito:
            carrito.detalles.all().delete()
            Bitacora.objects.create(
                usuario=request.user,
                accion="Vació su carrito de compras",
                ip=get_client_ip(request),
                estado=True
            )
            return Response({"message": "Carrito vaciado correctamente"}, status=status.HTTP_200_OK)
        return Response({"error": "No hay carrito activo"}, status=status.HTTP_404_NOT_FOUND)
