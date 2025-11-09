"""
Views adicionales para generación de reportes dinámicos mediante prompts.
Este archivo complementa el reporte/views.py existente.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.files.base import ContentFile
from django.utils import timezone

from reporte.models import Reporte
from reporte.serializers import ReporteSerializer
from reporte.utils import (
    generar_reporte_ventas_pdf,
    generar_reporte_ventas_excel,
    generar_datos_reporte_ventas
)
from reporte.views import ReporteViewSet
from bitacora.models import Bitacora
from users.views import get_client_ip
from .reporte_prompt_parser import interpretar_prompt
import json


#--------------------------------------
import speech_recognition as sr
import ffmpeg
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.test import APIRequestFactory

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_reporte_desde_audio(request):
    """
    Genera un reporte dinámico a partir de un archivo de audio (.wav o .mp3),
    transcribiéndolo automáticamente antes de generar el reporte.
    """
    archivo = request.FILES.get('archivo_audio')
    if not archivo:
        return Response(
            {'error': 'Debe enviar un archivo de audio (.wav o .mp3)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # 1️⃣ Guardar temporalmente el archivo subido
        temp_path = default_storage.save(f"temp/{archivo.name}", ContentFile(archivo.read()))
        full_path = os.path.join(default_storage.location, temp_path)
        wav_path = full_path

        # 2️⃣ Si el archivo es MP3, convertirlo a WAV con ffmpeg
        if archivo.name.lower().endswith('.mp3'):
            wav_path = full_path.replace('.mp3', '.wav')
            ffmpeg.input(full_path).output(wav_path).run(overwrite_output=True, quiet=True)

        # 3️⃣ Reconocer voz (transcripción)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            texto_transcrito = recognizer.recognize_google(audio_data, language='es-ES')

        # 4️⃣ Limpiar temporales
        default_storage.delete(temp_path)
        if wav_path != full_path and os.path.exists(wav_path):
            os.remove(wav_path)

        # 5️⃣ Reutilizar la lógica existente para generar el reporte
        factory = APIRequestFactory()
        fake_request = factory.post(
            '/api/reportes/generar-dinamico/',
            {'prompt': texto_transcrito, 'es_voz': True},
            format='json',
            HTTP_AUTHORIZATION=request.META.get('HTTP_AUTHORIZATION', '')
        )
        fake_request.user = request.user

        response = generar_reporte_dinamico(fake_request)

        # 6️⃣ Incluir transcripción en la respuesta
        if hasattr(response, 'data'):
            response.data['texto_transcrito'] = texto_transcrito

        return response

    except sr.UnknownValueError:
        return Response({'error': 'No se pudo entender el audio. Intente hablar más claro.'}, status=status.HTTP_400_BAD_REQUEST)
    except sr.RequestError as e:
        return Response({'error': f'Error al conectar con el servicio de reconocimiento: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': f'Error al procesar el audio: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_reporte_dinamico(request):
    """
    Genera un reporte interpretando un prompt en lenguaje natural.
    
    POST /api/reportes/generar-dinamico/
    
    Body:
    {
        "prompt": "Quiero un reporte de ventas del mes de septiembre, agrupado por producto, en PDF"
    }
    
    o con voz:
    {
        "prompt": "texto transcrito desde voz...",
        "es_voz": true
    }
    """
    prompt = request.data.get('prompt')
    es_voz = request.data.get('es_voz', False)
    
    if not prompt:
        return Response(
            {'error': 'Debe proporcionar un prompt'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # 1. Interpretar el prompt
        parametros = interpretar_prompt(prompt)
        
        # 2. Generar los datos según el tipo de reporte
        tipo = parametros.get('tipo', 'ventas')
        fecha_inicio = parametros.get('fecha_inicio')
        fecha_fin = parametros.get('fecha_fin')
        
        if tipo == 'ventas':
            datos_reporte = generar_datos_reporte_ventas(fecha_inicio, fecha_fin)
        elif tipo == 'productos':
            viewset = ReporteViewSet()
            datos_reporte = viewset._generar_datos_productos()
        elif tipo == 'clientes':
            viewset = ReporteViewSet()
            datos_reporte = viewset._generar_datos_clientes()
        elif tipo == 'inventario':
            viewset = ReporteViewSet()
            datos_reporte = viewset._generar_datos_inventario()
        elif tipo == 'financiero':
            viewset = ReporteViewSet()
            datos_reporte = viewset._generar_datos_financiero(fecha_inicio, fecha_fin)
        else:
            return Response(
                {'error': f'Tipo de reporte no soportado: {tipo}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. Aplicar filtros de agrupación si se especificaron
        agrupar_por = parametros.get('agrupar_por')
        if agrupar_por and tipo == 'ventas':
            datos_reporte = _aplicar_agrupacion(datos_reporte, agrupar_por)
        
        # 4. Filtrar campos si se especificaron
        campos = parametros.get('campos')
        if campos and tipo == 'ventas':
            datos_reporte = _filtrar_campos(datos_reporte, campos)
        
        # 5. Generar el archivo en el formato solicitado
        formato = parametros.get('formato', 'pdf')
        
        if formato == 'pdf':
            if tipo == 'ventas':
                archivo_buffer = generar_reporte_ventas_pdf(
                    datos_reporte,
                    fecha_inicio,
                    fecha_fin
                )
                nombre_archivo = f'reporte_ventas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                content_type = 'application/pdf'
        elif formato == 'excel':
            if tipo == 'ventas':
                archivo_buffer = generar_reporte_ventas_excel(
                    datos_reporte,
                    fecha_inicio,
                    fecha_fin
                )
                nombre_archivo = f'reporte_ventas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif formato == 'json':
            archivo_buffer = json.dumps(datos_reporte, indent=2, ensure_ascii=False).encode('utf-8')
            nombre_archivo = f'reporte_{tipo}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
            content_type = 'application/json'
        else:
            return Response(
                {'error': 'Formato no soportado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 6. Crear el registro del reporte
        descripcion = parametros.get('descripcion', f'Reporte generado desde prompt')
        if es_voz:
            descripcion += ' (comando de voz)'

        # 🔧 Asegurar que la descripción no exceda 100 caracteres
        if len(descripcion) > 100:
            descripcion = descripcion[:97] + "..."

        
        parametros_serializables = {}
        for k, v in parametros.items():
            # Si es lista o diccionario, mantenerlo igual
            if isinstance(v, (list, dict)):
                parametros_serializables[k] = v
            # Si tiene método isoformat (date, datetime)
            elif hasattr(v, "isoformat"):
                parametros_serializables[k] = v.isoformat()
            # Cualquier otro tipo lo convertimos a str
            else:
                parametros_serializables[k] = str(v)

        # --- 🧾 Crear registro del reporte ---
        reporte = Reporte.objects.create(
            tipo=tipo,
            descripcion=descripcion,
            generado_por=request.user,
            formato=formato,
            parametros={
                'prompt_original': prompt,
                'es_voz': es_voz,
                **parametros_serializables  # ✅ ya sin objetos "date"
            },
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        ) 
        
        # 7. Guardar el archivo
        if isinstance(archivo_buffer, bytes):
            content = ContentFile(archivo_buffer)
        else:
            content = ContentFile(archivo_buffer.read())
        
        reporte.archivo.save(nombre_archivo, content, save=True)
        
        # 8. Registrar en bitácora
        metodo = "comando de voz" if es_voz else "prompt de texto"
        Bitacora.objects.create(
            usuario=request.user,
            accion=f"Generó reporte dinámico de {tipo} mediante {metodo}: '{prompt[:50]}...'",
            ip=get_client_ip(request),
            estado=True
        )
        
        # 9. Retornar respuesta
        serializer = ReporteSerializer(reporte, context={'request': request})
        
        return Response({
            'mensaje': 'Reporte generado exitosamente desde prompt',
            'prompt_interpretado': parametros,
            'reporte': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Error al generar reporte: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_reporte_por_voz(request):
    """
    Genera un reporte a partir de un comando de voz transcrito.
    """
    texto_voz = request.data.get('texto_voz')

    if not texto_voz:
        return Response(
            {'error': 'Debe proporcionar el texto transcrito de la voz'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Creamos un request simulado con autenticación y cabeceras copiadas
    from rest_framework.test import APIRequestFactory
    factory = APIRequestFactory()

    fake_request = factory.post(
        '/api/reportes/generar-dinamico/',
        {
            'prompt': texto_voz,
            'es_voz': True
        },
        format='json',
        HTTP_AUTHORIZATION=request.META.get('HTTP_AUTHORIZATION', '')
    )

    # ✅ Asignamos manualmente el usuario autenticado
    fake_request.user = request.user

    # ✅ Llamamos al generador dinámico
    return generar_reporte_dinamico(fake_request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def interpretar_prompt_preview(request):
    """
    Interpreta un prompt sin generar el reporte.
    Útil para mostrar una vista previa de lo que se generará.
    
    POST /api/reportes/interpretar-prompt/
    
    Body:
    {
        "prompt": "Quiero un reporte de ventas de septiembre"
    }
    
    Response:
    {
        "parametros_interpretados": {
            "tipo": "ventas",
            "formato": "pdf",
            "fecha_inicio": "2025-09-01",
            ...
        },
        "confirmacion": "Se generará un reporte de ventas del 01/09/2025 al 30/09/2025 en formato PDF"
    }
    """
    prompt = request.data.get('prompt')
    
    if not prompt:
        return Response(
            {'error': 'Debe proporcionar un prompt'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        parametros = interpretar_prompt(prompt)
        
        # Generar mensaje de confirmación
        tipo = parametros.get('tipo', 'general')
        formato = parametros.get('formato', 'pdf')
        fecha_inicio = parametros.get('fecha_inicio')
        fecha_fin = parametros.get('fecha_fin')
        
        confirmacion = f"Se generará un reporte de {tipo}"
        
        if fecha_inicio and fecha_fin:
            confirmacion += f" del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"
        
        if parametros.get('agrupar_por'):
            confirmacion += f", agrupado por {parametros['agrupar_por']}"
        
        confirmacion += f" en formato {formato.upper()}"
        
        # Convertir dates a strings para JSON
        parametros_json = {**parametros}
        if fecha_inicio:
            parametros_json['fecha_inicio'] = str(fecha_inicio)
        if fecha_fin:
            parametros_json['fecha_fin'] = str(fecha_fin)
        
        return Response({
            'parametros_interpretados': parametros_json,
            'confirmacion': confirmacion
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error al interpretar prompt: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


# Funciones auxiliares

def _aplicar_agrupacion(datos_reporte, agrupar_por):
    """
    Agrupa los datos del reporte según el criterio especificado.
    
    Args:
        datos_reporte (dict): Datos del reporte
        agrupar_por (str): Campo por el cual agrupar
    
    Returns:
        dict: Datos agrupados
    """
    if 'ventas_detalle' not in datos_reporte:
        return datos_reporte
    
    from collections import defaultdict
    
    ventas = datos_reporte['ventas_detalle']
    grupos = defaultdict(lambda: {'total': 0, 'cantidad': 0, 'ventas': []})
    
    if agrupar_por == 'producto':
        # Necesitaríamos acceso a los detalles de venta por producto
        # Por simplicidad, retornamos los datos sin modificar
        pass
    elif agrupar_por == 'cliente':
        for venta in ventas:
            cliente = venta['usuario']
            grupos[cliente]['total'] += venta['total']
            grupos[cliente]['cantidad'] += 1
            grupos[cliente]['ventas'].append(venta)
        
        datos_reporte['ventas_por_cliente'] = dict(grupos)
    
    return datos_reporte


def _filtrar_campos(datos_reporte, campos):
    """
    Filtra los campos del reporte según lo solicitado.
    
    Args:
        datos_reporte (dict): Datos del reporte
        campos (list): Lista de campos a incluir
    
    Returns:
        dict: Datos filtrados
    """
    if 'ventas_detalle' not in datos_reporte:
        return datos_reporte
    
    ventas_filtradas = []
    
    for venta in datos_reporte['ventas_detalle']:
        venta_filtrada = {}
        
        for campo in campos:
            if campo == 'nombre_cliente':
                venta_filtrada['cliente'] = venta.get('usuario')
            elif campo == 'cantidad_compras':
                venta_filtrada['cantidad_compras'] = 1  # Cada registro es una compra
            elif campo == 'monto_total':
                venta_filtrada['monto_total'] = venta.get('total')
            elif campo == 'fechas':
                venta_filtrada['fecha'] = venta.get('fecha')
            elif campo == 'producto':
                venta_filtrada['producto'] = venta.get('producto', 'N/A')
        
        ventas_filtradas.append(venta_filtrada)
    
    datos_reporte['ventas_detalle'] = ventas_filtradas
    
    return datos_reporte