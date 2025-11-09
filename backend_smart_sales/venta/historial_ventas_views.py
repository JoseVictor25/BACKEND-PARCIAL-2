from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from venta.models import Venta, DetalleVenta
from venta.serializers import VentaSerializer
from bitacora.models import Bitacora
from users.views import get_client_ip


class HistorialVentasViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar el historial de ventas.
    
    Endpoints disponibles:
    - GET /api/historial-ventas/ - Listar todas las ventas
    - GET /api/historial-ventas/{id}/ - Ver detalle de una venta
    - GET /api/historial-ventas/mis-compras/ - Ver compras del usuario autenticado
    - GET /api/historial-ventas/estadisticas/ - Ver estadísticas de ventas
    - GET /api/historial-ventas/por-periodo/ - Filtrar ventas por período
    """
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna las ventas según el rol del usuario.
        - Clientes: solo sus propias ventas
        - Administradores: todas las ventas
        """
        user = self.request.user
        
        if user.is_superuser or (user.rol and user.rol.nombre.lower() in ['administrador', 'admin']):
            return Venta.objects.all().order_by('-fecha')
        
        return Venta.objects.filter(usuario=user).order_by('-fecha')

    def list(self, request, *args, **kwargs):
        """Lista las ventas con filtros opcionales."""
        queryset = self.get_queryset()
        
        # Filtros opcionales
        estado = request.query_params.get('estado')
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        usuario_id = request.query_params.get('usuario_id')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        
        if usuario_id and (request.user.is_superuser or 
                          (request.user.rol and request.user.rol.nombre.lower() in ['administrador', 'admin'])):
            queryset = queryset.filter(usuario_id=usuario_id)
        
        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'ventas': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='mis-compras')
    def mis_compras(self, request):
        """
        Retorna el historial de compras del usuario autenticado.
        
        GET /api/historial-ventas/mis-compras/
        Query params opcionales:
        - estado: filtrar por estado (pendiente, pagado, cancelado)
        - limite: cantidad de resultados (default: 20)
        """
        usuario = request.user
        limite = int(request.query_params.get('limite', 20))
        estado = request.query_params.get('estado')
        
        ventas = Venta.objects.filter(usuario=usuario).order_by('-fecha')[:limite]
        
        if estado:
            ventas = ventas.filter(estado=estado)
        
        serializer = self.get_serializer(ventas, many=True)
        
        # Calcular totales
        total_gastado = Venta.objects.filter(
            usuario=usuario,
            estado='pagado'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        cantidad_compras = Venta.objects.filter(
            usuario=usuario,
            estado='pagado'
        ).count()
        
        return Response({
            'resumen': {
                'total_gastado': float(total_gastado),
                'cantidad_compras': cantidad_compras,
                'ticket_promedio': float(total_gastado / cantidad_compras) if cantidad_compras > 0 else 0
            },
            'compras': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de ventas.
        Solo accesible para administradores.
        
        GET /api/historial-ventas/estadisticas/
        Query params opcionales:
        - periodo: 'hoy', 'semana', 'mes', 'año'
        """
        user = request.user
        
        # Verificar permisos de administrador
        if not (user.is_superuser or (user.rol and user.rol.nombre.lower() in ['administrador', 'admin'])):
            return Response(
                {'error': 'No tiene permisos para ver estadísticas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        periodo = request.query_params.get('periodo', 'mes')
        hoy = timezone.now()
        
        # Definir rango de fechas según el período
        if periodo == 'hoy':
            fecha_desde = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'semana':
            fecha_desde = hoy - timedelta(days=7)
        elif periodo == 'mes':
            fecha_desde = hoy - timedelta(days=30)
        elif periodo == 'año':
            fecha_desde = hoy - timedelta(days=365)
        else:
            fecha_desde = None
        
        # Filtrar ventas por período
        ventas_query = Venta.objects.filter(estado='pagado')
        if fecha_desde:
            ventas_query = ventas_query.filter(fecha__gte=fecha_desde)
        
        # Calcular estadísticas
        total_ventas = ventas_query.aggregate(total=Sum('total'))['total'] or 0
        cantidad_ventas = ventas_query.count()
        ticket_promedio = total_ventas / cantidad_ventas if cantidad_ventas > 0 else 0
        
        # Productos más vendidos
        productos_vendidos = DetalleVenta.objects.filter(
            venta__in=ventas_query
        ).values(
            'producto__nombre'
        ).annotate(
            total_vendido=Sum('cantidad'),
            ingresos=Sum('subtotal')
        ).order_by('-total_vendido')[:10]
        
        # Ventas por día
        ventas_por_dia = ventas_query.extra(
            select={'dia': 'DATE(fecha)'}
        ).values('dia').annotate(
            cantidad=Count('id'),
            total=Sum('total')
        ).order_by('dia')
        
        # Registrar en bitácora
        Bitacora.objects.create(
            usuario=request.user,
            accion=f"Consultó estadísticas de ventas del período: {periodo}",
            ip=get_client_ip(request),
            estado=True
        )
        
        return Response({
            'periodo': periodo,
            'resumen': {
                'total_ventas': float(total_ventas),
                'cantidad_ventas': cantidad_ventas,
                'ticket_promedio': float(ticket_promedio)
            },
            'productos_mas_vendidos': list(productos_vendidos),
            'ventas_por_dia': list(ventas_por_dia)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='por-periodo')
    def por_periodo(self, request):
        """
        Filtra ventas por período específico.
        
        GET /api/historial-ventas/por-periodo/?fecha_inicio=2025-01-01&fecha_fin=2025-12-31
        """
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response(
                {'error': 'Debe proporcionar fecha_inicio y fecha_fin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        )
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Calcular totales del período
        total_periodo = queryset.filter(estado='pagado').aggregate(
            total=Sum('total')
        )['total'] or 0
        
        return Response({
            'periodo': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            },
            'total_ventas': float(total_periodo),
            'cantidad_ventas': queryset.filter(estado='pagado').count(),
            'ventas': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """
        Cancela una venta y restaura el inventario.
        Solo administradores o el dueño de la venta pueden cancelar.
        
        POST /api/historial-ventas/{id}/cancelar/
        """
        venta = self.get_object()
        
        # Verificar permisos
        if not (request.user == venta.usuario or 
                request.user.is_superuser or 
                (request.user.rol and request.user.rol.nombre.lower() in ['administrador', 'admin'])):
            return Response(
                {'error': 'No tiene permisos para cancelar esta venta'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if venta.estado == 'cancelado':
            return Response(
                {'error': 'La venta ya está cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restaurar inventario
        from producto.models import Producto
        for detalle in venta.detalles.all():
            producto = detalle.producto
            producto.stock += detalle.cantidad
            producto.save()
        
        # Actualizar estado de la venta
        venta.estado = 'cancelado'
        venta.save()
        
        # Registrar en bitácora
        Bitacora.objects.create(
            usuario=request.user,
            accion=f"Canceló venta #{venta.id} y restauró inventario",
            ip=get_client_ip(request),
            estado=True
        )
        
        serializer = self.get_serializer(venta)
        
        return Response({
            'mensaje': 'Venta cancelada exitosamente. Inventario restaurado.',
            'venta': serializer.data
        }, status=status.HTTP_200_OK)