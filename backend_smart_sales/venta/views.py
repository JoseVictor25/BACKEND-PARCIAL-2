from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.db import transaction
from django.conf import settings
import stripe
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Venta, DetalleVenta , Garantia
from .serializers import VentaSerializer
from producto.models import Producto
from users.models import CustomUser
from users.views import get_client_ip
from bitacora.models import Bitacora

from rest_framework.decorators import action
from datetime import timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta  # Correcta importación de relativedelta

from datetime import datetime


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
    print("📦 Datos recibidos: - views.py:80", request.data)

    try:
        usuario = request.user
        data = request.data
        productos = data.get('productos', [])
        total = data.get('total')

        if not productos or not total:
            return Response({'error': 'Debe enviar productos y total.'}, status=status.HTTP_400_BAD_REQUEST)

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

            # Establecer la fecha de inicio como la fecha de la venta
            fecha_inicio = datetime.today().date()
            print(f"📅 Fecha de inicio: {fecha_inicio} - views.py:114")  # Verifica la fecha de inicio

            # Verifica el valor de producto.garantia
            if hasattr(producto, 'garantia'):
                print(f"🔑 Duración de la garantía en meses: {producto.garantia} - views.py:118")
            else:
                print("❌ El producto no tiene un campo 'garantia' definido correctamente. - views.py:120")

            try:
                # Crear la garantía
                garantia = Garantia.objects.create(
                    producto=producto,
                    venta=venta,
                    fecha_inicio=fecha_inicio,  # Establece la fecha de inicio como la fecha de la venta
                    fecha_fin=fecha_inicio + relativedelta(months=producto.garantia),  # Sumar la duración de la garantía
                    estado='activa',  # Estado inicial de la garantía
                )

                # Verifica si la garantía se creó correctamente
                print(f"✅ Garantía creada: Producto: {producto.nombre}, Fecha de inicio: {garantia.fecha_inicio}, Fecha de fin: {garantia.fecha_fin}, Estado: {garantia.estado} - views.py:133")

            except Exception as e:
                print(f"❌ Error al crear la garantía: {str(e)} - views.py:136")

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
        print("🧑‍💼 Usuario autenticado: - views.py:226", request.user.email if hasattr(request.user, 'email') else request.user)
        print("🧾 ID de la venta recibida: - views.py:227", venta_id)
        print("📩 Datos recibidos en el request: - views.py:228", request.data)

        # Solo admin o el creador puede editar
        if not (request.user.is_staff or request.user.is_superuser or venta.usuario == request.user):
            print("⛔ Permiso denegado al usuario: - views.py:232", request.user)
            return Response({'error': 'No tiene permisos para editar esta venta.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = VentaSerializer(venta, data=request.data, partial=True)

        if serializer.is_valid():
            print("✅ Datos validados correctamente. Campos válidos: - views.py:239", serializer.validated_data)
            serializer.save()
            print("💾 Venta actualizada exitosamente en BD. - views.py:241")

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
            print("⚠️ Error de validación en serializer: - views.py:257", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Venta.DoesNotExist:
        print("❌ Venta no encontrada con ID: - views.py:261", venta_id)
        return Response({'error': 'Venta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("💣 Error inesperado al editar venta: - views.py:264", str(e))
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)





