from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VentaViewSet, ProcesarPagoView, StripeWebhookView

router = DefaultRouter()
router.register(r'ventas', VentaViewSet, basename='venta')

urlpatterns = [
    path('', include(router.urls)),

    # Endpoint para iniciar el pago con Stripe
    path('procesar-pago/', ProcesarPagoView.as_view(), name='procesar_pago'),

    # Webhook de Stripe (para recibir notificaciones)
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
]
