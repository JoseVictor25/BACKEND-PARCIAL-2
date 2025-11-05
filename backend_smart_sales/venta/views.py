from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
import stripe
import os

from bitacora.models import Bitacora
from users.views import get_client_ip
from .models import Venta, DetalleVenta
from .serializers import VentaSerializer
from carrito.models import Carrito

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# 🧾 CREAR VENTA A PARTIR DEL CARRITO
class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all().order_by("-fecha")
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Mostrar solo las ventas del usuario actual
        return Venta.objects.filter(usuario=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            carrito = Carrito.objects.filter(usuario=request.user, activo=True).first()
            if not carrito or carrito.detalles.count() == 0:
                return Response(
                    {"error": "El carrito está vacío o no existe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            total = sum(item.subtotal() for item in carrito.detalles.all())
            venta = Venta.objects.create(usuario=request.user, total=total)

            for item in carrito.detalles.all():
                # Validar stock
                if item.producto.stock < item.cantidad:
                    raise ValueError(f"Stock insuficiente para {item.producto.nombre}")

                # Crear detalle de venta
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.producto.precio,
                    subtotal=item.subtotal(),
                )

                # Descontar stock
                item.producto.stock -= item.cantidad
                item.producto.save()

            # Desactivar carrito
            carrito.activo = False
            carrito.save()

            # Registrar en Bitácora
            Bitacora.objects.create(
                usuario=request.user,
                accion=f"Generó venta #{venta.id} por un total de {venta.total} Bs",
                ip=get_client_ip(request),
                estado=True,
            )

            return Response(VentaSerializer(venta).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# 💳 PROCESAR PAGO CON STRIPE
class ProcesarPagoView(APIView):
    """
    Crea un PaymentIntent de Stripe para la venta especificada.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            venta_id = request.data.get("venta_id")
            if not venta_id:
                return Response(
                    {"error": "Debe proporcionar el ID de la venta."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            venta = Venta.objects.get(id=venta_id, usuario=request.user)

            if venta.estado == "pagado":
                return Response(
                    {"error": "Esta venta ya fue pagada."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Crear el intento de pago en Stripe (monto en centavos)
            intent = stripe.PaymentIntent.create(
                amount=int(round(float(venta.total) * 100)),
                currency="usd",
                metadata={"venta_id": venta.id, "usuario": request.user.username},
                automatic_payment_methods={"enabled": True},
            )

            # Registrar intento de pago
            Bitacora.objects.create(
                usuario=request.user,
                accion=f"Intentó pagar la venta #{venta.id} ({venta.total} Bs)",
                ip=get_client_ip(request),
                estado=True,
            )

            return Response(
                {
                    "clientSecret": intent.client_secret,
                    "publicKey": settings.STRIPE_PUBLIC_KEY,
                    "venta": VentaSerializer(venta).data,
                },
                status=status.HTTP_200_OK,
            )

        except Venta.DoesNotExist:
            return Response(
                {"error": "Venta no encontrada."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ⚙️ WEBHOOK DE CONFIRMACIÓN DE STRIPE
@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """
    Recibe confirmaciones de Stripe (pago exitoso, fallido, etc.)
    """

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError:
            # Cuerpo inválido
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            # Firma no válida
            return HttpResponse(status=400)

        # ✅ Cuando el pago es exitoso
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            venta_id = payment_intent["metadata"].get("venta_id")
            if venta_id:
                venta = Venta.objects.filter(id=venta_id).first()
                if venta:
                    venta.estado = "pagado"
                    venta.save()
                    Bitacora.objects.create(
                        usuario=venta.usuario,
                        accion=f"Pago completado para venta #{venta.id}",
                        ip="Webhook Stripe",
                        estado=True,
                    )

        return HttpResponse(status=200)
