from django.urls import path
from . import views

urlpatterns = [
    path('stripe/probar/', views.probar_stripe_key, name='probar_stripe_key'),
    path('stripe/crear-pago/', views.crear_pago, name='crear_pago'),
    path('ventas/registrar/', views.registrar_venta, name='registrar_venta'),
]
