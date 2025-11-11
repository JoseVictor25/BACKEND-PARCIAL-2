from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django.core.files.base import ContentFile
from bitacora.models import Bitacora
from users.views import get_client_ip
from .models import Reporte
from .serializers import ReporteSerializer, ReporteCreateSerializer


from .utils import (
	generar_reporte_ventas_pdf,
	generar_reporte_ventas_excel,
	generar_datos_reporte_ventas,
	generar_reporte_productos_pdf,
	generar_reporte_productos_excel,
	generar_reporte_clientes_pdf,
	generar_reporte_clientes_excel,
	generar_reporte_inventario_pdf,
	generar_reporte_inventario_excel,
	generar_reporte_financiero_pdf,
	generar_reporte_financiero_excel,
)
import json


class ReporteViewSet(viewsets.ModelViewSet):
	queryset = Reporte.objects.all()
	serializer_class = ReporteSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		if self.request.user.is_superuser:
			return Reporte.objects.all()
		return Reporte.objects.filter(generado_por=self.request.user)

	# 👇👇 Mueve aquí el método generar (dentro de la clase, con indentación)
	@action(detail=False, methods=["post"], url_path="generar")
	def generar(self, request):
		print("🟢 [INICIO] Llamada a /api/reportes/generar/ - views.py:43")

		serializer = ReporteCreateSerializer(data=request.data)
		print(f"📦 Datos recibidos: {request.data} - views.py:46")

		if not serializer.is_valid():
			print("❌ Error de validación: - views.py:49", serializer.errors)
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		data = serializer.validated_data
		tipo = data["tipo"]
		formato = data["formato"]
		fecha_inicio = data.get("fecha_inicio")
		fecha_fin = data.get("fecha_fin")
		descripcion = data.get("descripcion", f"Reporte de {tipo}")

		print(f"🧾 Tipo: {tipo} | Formato: {formato} - views.py:59")
		print(f"🗓️ Periodo: {fecha_inicio} → {fecha_fin} - views.py:60")
		print(f"📝 Descripción: {descripcion} - views.py:61")

		try:
			print("⚙️ Generando datos del reporte... - views.py:64")

			if tipo == "ventas":
				datos_reporte = generar_datos_reporte_ventas(fecha_inicio, fecha_fin)
			elif tipo == "productos":
				datos_reporte = self._generar_datos_productos()
			elif tipo == "clientes":
				datos_reporte = self._generar_datos_clientes()
			elif tipo == "inventario":
				datos_reporte = self._generar_datos_inventario()
			elif tipo == "financiero":
				datos_reporte = self._generar_datos_financiero(fecha_inicio, fecha_fin)
			else:
				print("🚫 Tipo de reporte no soportado: - views.py:77", tipo)
				return Response(
					{"error": "Tipo de reporte no soportado"},
					status=status.HTTP_400_BAD_REQUEST,
				)

			print(
				f"✅ Datos del reporte generados correctamente. Claves: {list(datos_reporte.keys())}"
			)

			print(f"🧩 Generando archivo en formato {formato.upper()}... - views.py:87")

			archivo_buffer = None
			nombre_archivo = None
			content_type = None

			if formato == "pdf":
				if tipo == "ventas":
					archivo_buffer = generar_reporte_ventas_pdf(
						datos_reporte, fecha_inicio, fecha_fin
					)
					nombre_archivo = (
						f'reporte_ventas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
					)
					content_type = "application/pdf"

				elif tipo == "productos":
					archivo_buffer = generar_reporte_productos_pdf(datos_reporte)
					nombre_archivo = f'reporte_productos_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
					content_type = "application/pdf"

				elif tipo == "clientes":  # ✅ nuevo bloque
					archivo_buffer = generar_reporte_clientes_pdf(datos_reporte)
					nombre_archivo = f'reporte_clientes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
					content_type = "application/pdf"

				elif tipo == "inventario":
					archivo_buffer = generar_reporte_inventario_pdf(datos_reporte)
					nombre_archivo = f'reporte_inventario_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
					content_type = "application/pdf"

				elif tipo == "financiero":  # ✅ nuevo bloque
					archivo_buffer = generar_reporte_financiero_pdf(
						datos_reporte,
						incluir_graficos=data.get("incluir_graficos", True),
					)
					nombre_archivo = f'reporte_financiero_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
					content_type = "application/pdf"

			elif formato == "excel":
				if tipo == "ventas":
					archivo_buffer = generar_reporte_ventas_excel(
						datos_reporte, fecha_inicio, fecha_fin
					)
					nombre_archivo = f'reporte_ventas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
					content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

				elif tipo == "productos":  # ✅ nuevo bloque
					archivo_buffer = generar_reporte_productos_excel(datos_reporte)
					nombre_archivo = f'reporte_productos_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
					content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

				elif tipo == "clientes":  # ✅ con gráficos opcionales
					archivo_buffer = generar_reporte_clientes_excel(
						datos_reporte,
						incluir_graficos=data.get("incluir_graficos", True),
					)
					nombre_archivo = f'reporte_clientes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
					content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

				elif tipo == "inventario":  # ✅ nuevo bloque
					archivo_buffer = generar_reporte_inventario_excel(
						datos_reporte,
						incluir_graficos=data.get("incluir_graficos", True),
					)
					nombre_archivo = f'reporte_inventario_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
					content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
				elif tipo == "financiero":  # ✅ nuevo bloque
					archivo_buffer = generar_reporte_financiero_excel(
						datos_reporte,
						incluir_graficos=data.get("incluir_graficos", True),
					)
					nombre_archivo = f'reporte_financiero_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
					content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

			elif formato == "json":
				archivo_buffer = json.dumps(
					datos_reporte, indent=2, ensure_ascii=False
				).encode("utf-8")
				nombre_archivo = (
					f'reporte_{tipo}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
				)
				content_type = "application/json"

			else:
				print("🚫 Formato no soportado: - views.py:172", formato)
				return Response(
					{"error": "Formato no soportado"},
					status=status.HTTP_400_BAD_REQUEST,
				)

			if not archivo_buffer:
				print(
					"❌ ERROR: No se generó el archivo correctamente (archivo_buffer vacío)."
				)
				return Response(
					{
						"error": "No se pudo generar el archivo para el tipo y formato seleccionados."
					},
					status=status.HTTP_400_BAD_REQUEST,
				)

			print("✅ Archivo generado correctamente: - views.py:189", nombre_archivo)

			print(
				"💾 Guardando registro del reporte en la base de datos..."
			)

			reporte = Reporte.objects.create(
				tipo=tipo,
				descripcion=descripcion,
				generado_por=request.user,
				formato=formato,
				parametros={
					"fecha_inicio": str(fecha_inicio) if fecha_inicio else None,
					"fecha_fin": str(fecha_fin) if fecha_fin else None,
					"incluir_graficos": data.get("incluir_graficos", True),
					"agrupar_por": data.get("agrupar_por", ""),
				},
				fecha_inicio=fecha_inicio,
				fecha_fin=fecha_fin,
			)

			print(f"🆔 Reporte creado con ID: {reporte.id} - views.py:210")

			print("📂 Guardando archivo en MEDIA_ROOT... - views.py:212")

			if isinstance(archivo_buffer, bytes):
				content = ContentFile(archivo_buffer)
			else:
				content = ContentFile(archivo_buffer.read())

			reporte.archivo.save(nombre_archivo, content, save=True)
			print(f"📁 Archivo guardado en: {reporte.archivo.path} - views.py:220")

			print("🪶 Registrando acción en bitácora... - views.py:222")

			Bitacora.objects.create(
				usuario=request.user,
				accion=f"Generó reporte de {tipo} en formato {formato}",
				ip=get_client_ip(request),
				estado=True,
			)

			print("✅ Bitácora registrada correctamente. - views.py:231")
			response_serializer = ReporteSerializer(
				reporte, context={"request": request}
			)
			print("🎉 Reporte generado con éxito. - views.py:235")

			return Response(
				{
					"mensaje": "Reporte generado exitosamente",
					"reporte": response_serializer.data,
				},
				status=status.HTTP_201_CREATED,
			)

		except Exception as e:
			print("💥 ERROR FATAL al generar el reporte: - views.py:246")
			import traceback

			traceback.print_exc()
			return Response(
				{"error": f"Error al generar reporte: {str(e)}"},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)

	@action(detail=True, methods=["get"], url_path="descargar")
	def descargar(self, request, pk=None):
		"""
		Descarga el archivo de un reporte específico.

		GET /api/reportes/{id}/descargar/
		"""
		print(f"📥 Entrando en ReporteViewSet.descargar() con pk={pk} - views.py:262")

		reporte = self.get_object()
		print(f"🔍 Reporte encontrado: {reporte.id}  {reporte.descripcion} - views.py:265")

		if not reporte.archivo:
			print("⚠️ El reporte no tiene archivo asociado. - views.py:268")
			return Response(
				{"error": "El reporte no tiene archivo asociado"},
				status=status.HTTP_404_NOT_FOUND,
			)

		# Registrar en bitácora
		Bitacora.objects.create(
			usuario=request.user,
			accion=f"Descargó reporte ID {reporte.id}",
			ip=get_client_ip(request),
			estado=True,
		)
		print(f"📝 Bitácora registrada para el usuario: {request.user.username} - views.py:281")

		# Determinar el content type según el formato
		content_types = {
			"pdf": "application/pdf",
			"excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
			"json": "application/json",
		}

		content_type = content_types.get(reporte.formato, "application/octet-stream")
		print(f"📄 Tipo de contenido: {content_type} - views.py:291")

		response = FileResponse(
			reporte.archivo.open("rb"),
			content_type=content_type,
		)
		response["Content-Disposition"] = (
			f'attachment; filename="{reporte.archivo.name.split("/")[-1]}"'
		)

		print(f"✅ Archivo listo para descargar: {reporte.archivo.name} - views.py:301")
		return response


	@action(detail=False, methods=["get"], url_path="historial")
	def historial(self, request):
		"""
		Retorna el historial de reportes del usuario autenticado.

		GET /api/reportes/historial/
		Query params opcionales:
		- tipo: filtrar por tipo de reporte
		- formato: filtrar por formato
		- fecha_desde: filtrar desde fecha
		"""
		queryset = self.get_queryset()

		# Filtros opcionales
		tipo = request.query_params.get("tipo")
		formato = request.query_params.get("formato")
		fecha_desde = request.query_params.get("fecha_desde")

		if tipo:
			queryset = queryset.filter(tipo=tipo)
		if formato:
			queryset = queryset.filter(formato=formato)
		if fecha_desde:
			queryset = queryset.filter(fecha_generacion__gte=fecha_desde)

		serializer = self.get_serializer(queryset, many=True)

		return Response(
			{"count": queryset.count(), "reportes": serializer.data},
			status=status.HTTP_200_OK,
		)

	def perform_destroy(self, instance):
		"""Registra la eliminación de un reporte en la bitácora."""
		Bitacora.objects.create(
			usuario=self.request.user,
			accion=f"Eliminó reporte ID {instance.id} de tipo {instance.get_tipo_display()}",
			ip=get_client_ip(self.request),
			estado=True,
		)

		# Eliminar el archivo físico si existe
		if instance.archivo:
			instance.archivo.delete()

		instance.delete()

	# Métodos auxiliares para generar datos de otros tipos de reportes

	def _generar_datos_productos(self):
		"""Genera datos para reporte de productos."""
		from producto.models import Producto
		from django.db.models import Sum

		productos = Producto.objects.filter(estado=True)

		productos_data = []
		for producto in productos:
			productos_data.append(
				{
					"id": producto.id,
					"nombre": producto.nombre,
					"marca": producto.marca.nombre,
					"categoria": producto.categoria.nombre,
					"precio": float(producto.precio),
					"stock": producto.stock,
					"estado": "Activo" if producto.estado else "Inactivo",
				}
			)

		return {
			"total_productos": productos.count(),
			"valor_inventario": float(sum(p.precio * p.stock for p in productos)),
			"productos": productos_data,
		}

	def _generar_datos_clientes(self):
		"""Genera datos para reporte de clientes."""
		from users.models import CustomUser
		from venta.models import Venta
		from django.db.models import Sum, Count

		clientes = CustomUser.objects.filter(rol__nombre__iexact="Cliente")

		clientes_data = []
		for cliente in clientes:
			ventas = Venta.objects.filter(usuario=cliente, estado="pagado")
			total_compras = ventas.aggregate(total=Sum("total"))["total"] or 0
			cantidad_compras = ventas.count()

			clientes_data.append(
				{
					"id": cliente.id,
					"username": cliente.username,
					"email": cliente.email,
					"cantidad_compras": cantidad_compras,
					"total_compras": float(total_compras),
					"fecha_registro": cliente.date_joined.strftime("%d/%m/%Y"),
				}
			)

		return {"total_clientes": clientes.count(), "clientes": clientes_data}

	def _generar_datos_inventario(self):
		"""Genera datos para reporte de inventario."""
		from producto.models import Producto
		from django.db.models import Sum

		productos = Producto.objects.filter(estado=True)

		# Productos con bajo stock (menos de 10 unidades)
		bajo_stock = productos.filter(stock__lt=10)

		# Productos sin stock
		sin_stock = productos.filter(stock=0)

		return {
			"total_productos": productos.count(),
			"productos_bajo_stock": bajo_stock.count(),
			"productos_sin_stock": sin_stock.count(),
			"valor_total_inventario": float(sum(p.precio * p.stock for p in productos)),
			"productos_bajo_stock_detalle": [
				{"nombre": p.nombre, "stock": p.stock, "precio": float(p.precio)}
				for p in bajo_stock
			],
		}

	def _generar_datos_financiero(self, fecha_inicio=None, fecha_fin=None):
		"""Genera datos para reporte financiero."""
		from venta.models import Venta
		from django.db.models import Sum, Count, Avg

		ventas_query = Venta.objects.filter(estado="pagado")

		if fecha_inicio:
			ventas_query = ventas_query.filter(fecha__gte=fecha_inicio)
		if fecha_fin:
			ventas_query = ventas_query.filter(fecha__lte=fecha_fin)

		ingresos_totales = ventas_query.aggregate(total=Sum("total"))["total"] or 0

		return {
			"ingresos_totales": float(ingresos_totales),
			"cantidad_transacciones": ventas_query.count(),
			"ticket_promedio": float(
				ingresos_totales / ventas_query.count()
				if ventas_query.count() > 0
				else 0
			),
			"periodo": {
				"fecha_inicio": str(fecha_inicio) if fecha_inicio else None,
				"fecha_fin": str(fecha_fin) if fecha_fin else None,
			},
		}
