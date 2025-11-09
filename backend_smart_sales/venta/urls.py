from django.urls import path
from . import views

urlpatterns = [

    path('ventas/', views.listar_ventas, name='listar_ventas'),
    path('ventas/<int:venta_id>/', views.obtener_venta, name='obtener_venta'),
    path('ventas/<int:venta_id>/editar/', views.editar_venta, name='editar_venta'),




    path('stripe/probar/', views.probar_stripe_key, name='probar_stripe_key'),
    path('stripe/crear-pago/', views.crear_pago, name='crear_pago'),
    path('ventas/registrar/', views.registrar_venta, name='registrar_venta'),
]
