from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.db import transaction
from django.conf import settings
import stripe

from .models import Venta, DetalleVenta
from .serializers import VentaSerializer
from producto.models import Producto
from users.models import CustomUser
from users.views import get_client_ip
from bitacora.models import Bitacora

from rest_framework.decorators import action
from datetime import timedelta
from django.utils import timezone



# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# ✅ PROBAR CLAVE DE STRIPE
@api_view(['GET'])
def probar_stripe_key(request):
    return Response({"stripe_key_ok": bool(stripe.api_key)})


# 💳 CREAR INTENTO DE PAGO CON STRIPE
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_pago(request):
    """
    Crea un PaymentIntent en Stripe y devuelve el client_secret
    que el frontend usará para confirmar el pago.
    """
    try:
        monto = request.data.get('monto')
        if not monto:
            return Response({'error': 'El monto es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        intent = stripe.PaymentIntent.create(
            amount=int(monto*100),  # en centavos (5000 = $50.00)
            currency='usd',
            payment_method_types=['card']
        )

        return Response({'client_secret': intent.client_secret}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 🧾 REGISTRAR VENTA (después de pago exitoso)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def registrar_venta(request):
    """
    Registra una venta y sus detalles, actualizando inventario.
    Se llama después de confirmar el pago exitoso.
    """
    print("📦 Datos recibidos:", request.data)

    try:
        usuario = request.user
        data = request.data
        productos = data.get('productos', [])
        total = data.get('total')

        if not productos or not total:
            return Response({'error': 'Debe enviar productos y total.'}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar el cliente relacionado al usuario
        cliente = usuario

        # Crear la venta
        venta = Venta.objects.create(usuario=usuario, total=total, estado="pagado")

        # Crear los detalles
        for item in productos:
            producto = Producto.objects.get(id=item['producto_id'])
            cantidad = int(item['cantidad'])

            if producto.stock < cantidad:
                raise ValueError(f"Stock insuficiente para {producto.nombre}")

            subtotal = producto.precio * cantidad

            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=subtotal,
            )

            # Actualizar inventario
            producto.stock -= cantidad
            producto.save()

        # Registrar en bitácora
        Bitacora.objects.create(
            usuario=usuario,
            accion=f"Registró venta #{venta.id} por un total de {venta.total} USD",
            ip=get_client_ip(request),
            estado=True,
        )

        return Response({
            'mensaje': '✅ Venta registrada con éxito.',
            'venta': VentaSerializer(venta).data
        }, status=status.HTTP_201_CREATED)

    except CustomUser.DoesNotExist:
        return Response({'error': 'Cliente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

############################## 
# VIEWSET HISTORIAL DE VENTAS #
