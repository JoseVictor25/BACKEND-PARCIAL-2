from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from bitacora.models import Bitacora
from users.views import get_client_ip
from .models import Descuento
from .serializers import DescuentoSerializer, DescuentoCreateSerializer


class DescuentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar promociones y descuentos.
    
    Endpoints disponibles:
    - GET /api/descuentos/ - Listar todos los descuentos
    - POST /api/descuentos/ - Crear nuevo descuento
    - GET /api/descuentos/{id}/ - Ver detalle de descuento
    - PUT /api/descuentos/{id}/ - Actualizar descuento
    - DELETE /api/descuentos/{id}/ - Eliminar descuento
    - GET /api/descuentos/vigentes/ - Listar descuentos vigentes
    - GET /api/descuentos/por_producto/{producto_id}/ - Descuentos de un producto
    """
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer

    def get_permissions(self):
        """
        Permisos: lectura pública, escritura autenticada.
        """
        if self.action in ['list', 'retrieve', 'vigentes', 'por_producto']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """Usa serializer simplificado para crear/actualizar."""
        if self.action in ['create', 'update', 'partial_update']:
            return DescuentoCreateSerializer
        return DescuentoSerializer

    def perform_create(self, serializer):
        """Registra la creación de un descuento en la bitácora."""
        descuento = serializer.save()
        
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Creó descuento: {descuento.porcentaje}% para {descuento.producto.nombre if descuento.producto else 'General'}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_update(self, serializer):
        """Registra la actualización de un descuento en la bitácora."""
        descuento = serializer.save()
        
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Actualizó descuento ID {descuento.id}",
            ip=get_client_ip(self.request),
            estado=True
        )

    def perform_destroy(self, instance):
        """Registra la eliminación de un descuento en la bitácora."""
        producto_nombre = instance.producto.nombre if instance.producto else "General"
        
        Bitacora.objects.create(
            usuario=self.request.user,
            accion=f"Eliminó descuento: {instance.porcentaje}% de {producto_nombre}",
            ip=get_client_ip(self.request),
            estado=True
        )
        
        instance.delete()

    @action(detail=False, methods=['get'], url_path='vigentes')
    def vigentes(self, request):
        """
        Retorna solo los descuentos vigentes en la fecha actual.
        
        GET /api/descuentos/vigentes/
        """
        hoy = timezone.now().date()
        descuentos_vigentes = Descuento.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        )
        
        serializer = self.get_serializer(descuentos_vigentes, many=True)
        
        return Response({
            'count': descuentos_vigentes.count(),
            'descuentos': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='por-producto/(?P<producto_id>[^/.]+)')
    def por_producto(self, request, producto_id=None):
        """
        Retorna los descuentos vigentes de un producto específico.
        
        GET /api/descuentos/por-producto/{producto_id}/
        """
        from producto.models import Producto
        
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        hoy = timezone.now().date()
        descuentos = Descuento.objects.filter(
            producto=producto,
            activo=True,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        )
        
        serializer = self.get_serializer(descuentos, many=True)
        
        # Calcular precio con descuento si hay alguno vigente
        precio_original = producto.precio
        precio_con_descuento = precio_original
        
        if descuentos.exists():
            # Tomar el descuento con mayor porcentaje
            mejor_descuento = descuentos.order_by('-porcentaje').first()
            precio_con_descuento = mejor_descuento.calcular_precio_con_descuento(precio_original)
        
        return Response({
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio_original': float(precio_original),
                'precio_con_descuento': float(precio_con_descuento),
                'ahorro': float(precio_original - precio_con_descuento)
            },
            'descuentos': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='activar')
    def activar(self, request, pk=None):
        """
        Activa un descuento.
        
        POST /api/descuentos/{id}/activar/
        """
        descuento = self.get_object()
        descuento.activo = True
        descuento.save()
        
        Bitacora.objects.create(
            usuario=request.user,
            accion=f"Activó descuento ID {descuento.id}",
            ip=get_client_ip(request),
            estado=True
        )
        
        return Response(
            {'mensaje': 'Descuento activado exitosamente'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='desactivar')
    def desactivar(self, request, pk=None):
        """
        Desactiva un descuento.
        
        POST /api/descuentos/{id}/desactivar/
        """
        descuento = self.get_object()
        descuento.activo = False
        descuento.save()
        
        Bitacora.objects.create(
            usuario=request.user,
            accion=f"Desactivó descuento ID {descuento.id}",
            ip=get_client_ip(request),
            estado=True
        )
        
        return Response(
            {'mensaje': 'Descuento desactivado exitosamente'},
            status=status.HTTP_200_OK
        )


