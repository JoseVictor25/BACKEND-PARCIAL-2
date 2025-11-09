from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
<<<<<<< HEAD
from rest_framework import status
=======
from rest_framework import viewsets, status
>>>>>>> main
from django.db import transaction
from django.conf import settings
import stripe

from .models import Venta, DetalleVenta
from .serializers import VentaSerializer
from producto.models import Producto
from users.models import CustomUser
from users.views import get_client_ip
from bitacora.models import Bitacora

<<<<<<< HEAD
=======
from rest_framework.decorators import action
from datetime import timedelta
from django.utils import timezone



>>>>>>> main
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

<<<<<<< HEAD






# 📋 LISTAR TODAS LAS VENTAS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_ventas(request):
    """
    Lista todas las ventas registradas.
    Si el usuario no es admin, solo ve sus propias ventas.
    """
    try:
        usuario = request.user

        # Si el usuario es admin, ve todas las ventas
        if usuario.is_staff or usuario.is_superuser:
            ventas = Venta.objects.all().order_by('-id')
        else:
            ventas = Venta.objects.filter(usuario=usuario).order_by('-id')

        serializer = VentaSerializer(ventas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# 🔍 OBTENER DETALLE DE UNA VENTA
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_venta(request, venta_id):
    """
    Devuelve los detalles de una venta específica.
    """
    try:
        venta = Venta.objects.get(id=venta_id)

        # Solo el usuario dueño o un admin puede verla
        if not (request.user.is_staff or request.user.is_superuser or venta.usuario == request.user):
            return Response({'error': 'No tiene permisos para ver esta venta.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = VentaSerializer(venta)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Venta.DoesNotExist:
        return Response({'error': 'Venta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ✏️ EDITAR (ACTUALIZAR) UNA VENTA
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def editar_venta(request, venta_id):
    """
    Permite modificar el estado o detalles de una venta.
    Generalmente para actualizar estado (ej: entregado, cancelado, etc.)
    """
    try:
        venta = Venta.objects.get(id=venta_id)

        # ✅ Debug info: qué usuario hace la petición
        print("🧑‍💼 Usuario autenticado:", request.user.email if hasattr(request.user, 'email') else request.user)
        print("🧾 ID de la venta recibida:", venta_id)
        print("📩 Datos recibidos en el request:", request.data)

        # Solo admin o el creador puede editar
        if not (request.user.is_staff or request.user.is_superuser or venta.usuario == request.user):
            print("⛔ Permiso denegado al usuario:", request.user)
            return Response({'error': 'No tiene permisos para editar esta venta.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = VentaSerializer(venta, data=request.data, partial=True)

        if serializer.is_valid():
            print("✅ Datos validados correctamente. Campos válidos:", serializer.validated_data)
            serializer.save()
            print("💾 Venta actualizada exitosamente en BD.")

            # Registrar en bitácora
            Bitacora.objects.create(
                usuario=request.user,
                accion=f"Editó la venta #{venta.id}",
                ip=get_client_ip(request),
                estado=True,
            )

            return Response({
                'mensaje': '✅ Venta actualizada correctamente.',
                'venta': serializer.data
            }, status=status.HTTP_200_OK)

        else:
            print("⚠️ Error de validación en serializer:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Venta.DoesNotExist:
        print("❌ Venta no encontrada con ID:", venta_id)
        return Response({'error': 'Venta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("💣 Error inesperado al editar venta:", str(e))
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
=======
############################## 
# VIEWSET HISTORIAL DE VENTAS #
>>>>>>> main
