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
    generar_datos_reporte_ventas,
    generar_reporte_productos_pdf,
    generar_reporte_clientes_pdf,
    generar_reporte_inventario_pdf,
    generar_reporte_financiero_pdf,

    generar_reporte_productos_excel,
    generar_reporte_clientes_excel,
    generar_reporte_inventario_excel,
    generar_reporte_financiero_excel
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
    print("🎧 [DEBUG] Entrando a generar_reporte_desde_audio() - reporte_dinamico_views.py:49")
    archivo = request.FILES.get('archivo_audio')
    print(f"📥 [DEBUG] Archivo recibido: {archivo.name if archivo else 'Ninguno'} - reporte_dinamico_views.py:51")

    if not archivo:
        print("⚠️ [ERROR] No se recibió archivo de audio. - reporte_dinamico_views.py:54")
        return Response(
            {'error': 'Debe enviar un archivo de audio (.wav o .mp3)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # 1️⃣ Guardar temporalmente el archivo subido
        print("💾 [DEBUG] Guardando archivo temporalmente... - reporte_dinamico_views.py:62")
        temp_path = default_storage.save(f"temp/{archivo.name}", ContentFile(archivo.read()))
        full_path = os.path.join(default_storage.location, temp_path)
        wav_path = full_path
        print(f"📂 [DEBUG] Archivo guardado en: {full_path} - reporte_dinamico_views.py:66")

        # 2️⃣ Si el archivo es MP3, convertirlo a WAV con ffmpeg
        if archivo.name.lower().endswith('.mp3'):
            wav_path = full_path.replace('.mp3', '.wav')
            print(f"🎼 [DEBUG] Convirtiendo MP3 → WAV en: {wav_path} - reporte_dinamico_views.py:71")
            ffmpeg.input(full_path).output(wav_path).run(overwrite_output=True, quiet=True)
            print("✅ [DEBUG] Conversión completada correctamente. - reporte_dinamico_views.py:73")

        # 3️⃣ Reconocer voz (transcripción)
        print("🎙️ [DEBUG] Iniciando reconocimiento de voz (Google Speech)... - reporte_dinamico_views.py:76")
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            print("🔊 [DEBUG] Cargando datos de audio... - reporte_dinamico_views.py:79")
            audio_data = recognizer.record(source)
            print("🧠 [DEBUG] Procesando transcripción... - reporte_dinamico_views.py:81")
            texto_transcrito = recognizer.recognize_google(audio_data, language='es-ES')
            print(f"✅ [DEBUG] Texto transcrito: {texto_transcrito} - reporte_dinamico_views.py:83")

        # 4️⃣ Limpiar temporales
        print("🧹 [DEBUG] Eliminando archivos temporales... - reporte_dinamico_views.py:86")
        default_storage.delete(temp_path)
        if wav_path != full_path and os.path.exists(wav_path):
            os.remove(wav_path)
            print(f"🗑️ [DEBUG] Archivo temporal WAV eliminado: {wav_path} - reporte_dinamico_views.py:90")

        # 5️⃣ Reutilizar la lógica existente para generar el reporte
        print("📤 [DEBUG] Preparando request simulado para generar_reporte_dinamico()... - reporte_dinamico_views.py:93")
        factory = APIRequestFactory()
        fake_request = factory.post(
            '/api/reportes/generar-dinamico/',
            {'prompt': texto_transcrito, 'es_voz': True},
            format='json',
            HTTP_AUTHORIZATION=request.META.get('HTTP_AUTHORIZATION', '')
        )
        fake_request.user = request.user
        print(f"👤 [DEBUG] Usuario autenticado asignado: {request.user} - reporte_dinamico_views.py:102")

        print("🚀 [DEBUG] Llamando a generar_reporte_dinamico(fake_request)... - reporte_dinamico_views.py:104")
        response = generar_reporte_dinamico(fake_request)
        print("✅ [DEBUG] generar_reporte_dinamico ejecutado correctamente. - reporte_dinamico_views.py:106")

        # 6️⃣ Incluir transcripción en la respuesta
        if hasattr(response, 'data'):
            response.data['texto_transcrito'] = texto_transcrito
            print("📝 [DEBUG] Texto transcrito agregado a la respuesta final. - reporte_dinamico_views.py:111")

        print("📦 [DEBUG] Respuesta lista para enviar al cliente. - reporte_dinamico_views.py:113")
        return response

    except sr.UnknownValueError:
        print("💥 [ERROR] El servicio de reconocimiento no entendió el audio. - reporte_dinamico_views.py:117")
        return Response(
            {'error': 'No se pudo entender el audio. Intente hablar más claro.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except sr.RequestError as e:
        print(f"💥 [ERROR] Falla al conectar con el servicio de reconocimiento: {e} - reporte_dinamico_views.py:123")
        return Response(
            {'error': f'Error al conectar con el servicio de reconocimiento: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        print("💥 [ERROR] Excepción general en generar_reporte_desde_audio(): - reporte_dinamico_views.py:129")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error al procesar el audio: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



################################################################################################################################################################################333
####################################################################################################################################################################################
###################################################################################################################################################################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_reporte_dinamico(request):
    """
    Genera un reporte interpretando un prompt en lenguaje natural.
    """
    print("🚀 [DEBUG] Entrando a generar_reporte_dinamico() - reporte_dinamico_views.py:148")
    print(f"📥 [DEBUG] request.data: {request.data} - reporte_dinamico_views.py:149")

    prompt = request.data.get('prompt')
    es_voz = request.data.get('es_voz', False)
    print(f"🎙️ [DEBUG] prompt='{prompt}', es_voz={es_voz} - reporte_dinamico_views.py:153")

    if not prompt:
        print("⚠️ [ERROR] No se proporcionó un prompt. - reporte_dinamico_views.py:156")
        return Response(
            {'error': 'Debe proporcionar un prompt'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # 1️⃣ Interpretar el prompt
        print("🧠 [DEBUG] Interpretando prompt con IA... - reporte_dinamico_views.py:164")
        parametros = interpretar_prompt(prompt, use_ai=True)
        print(f"✅ [DEBUG] Parámetros interpretados: {parametros} - reporte_dinamico_views.py:166")

        # 2️⃣ Generar datos según el tipo
        tipo = parametros.get('tipo', 'ventas')
        fecha_inicio = parametros.get('fecha_inicio')
        fecha_fin = parametros.get('fecha_fin')
        print(f"📅 [DEBUG] tipo={tipo}, fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin} - reporte_dinamico_views.py:172")

        if tipo == 'ventas':
            print("📊 [DEBUG] Generando datos de ventas... - reporte_dinamico_views.py:175")
            datos_reporte = generar_datos_reporte_ventas(fecha_inicio, fecha_fin)
        elif tipo == 'productos':
            print("📦 [DEBUG] Generando datos de productos... - reporte_dinamico_views.py:178")
            viewset = ReporteViewSet()
            datos_reporte = viewset._generar_datos_productos()
        elif tipo == 'clientes':
            print("👥 [DEBUG] Generando datos de clientes... - reporte_dinamico_views.py:182")
            viewset = ReporteViewSet()
            datos_reporte = viewset._generar_datos_clientes()
        elif tipo == 'inventario':
            print("📦 [DEBUG] Generando datos de inventario... - reporte_dinamico_views.py:186")
            viewset = ReporteViewSet()
            datos_reporte = viewset._generar_datos_inventario()
        elif tipo == 'financiero':
            print("💰 [DEBUG] Generando datos financieros... - reporte_dinamico_views.py:190")
            viewset = ReporteViewSet()
            datos_reporte = viewset._generar_datos_financiero(fecha_inicio, fecha_fin)
        else:
            print(f"⚠️ [ERROR] Tipo de reporte no soportado: {tipo} - reporte_dinamico_views.py:194")
            return Response(
                {'error': f'Tipo de reporte no soportado: {tipo}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"✅ [DEBUG] Datos del reporte generados. Claves: {list(datos_reporte.keys())} - reporte_dinamico_views.py:200")

        # 3️⃣ Agrupar si se especificó
        agrupar_por = parametros.get('agrupar_por')
        if agrupar_por and tipo == 'ventas':
            print(f"📚 [DEBUG] Aplicando agrupación por: {agrupar_por} - reporte_dinamico_views.py:205")
            datos_reporte = _aplicar_agrupacion(datos_reporte, agrupar_por)

        # 4️⃣ Filtrar campos si se especificaron
        campos = parametros.get('campos')
        if campos and tipo == 'ventas':
            print(f"🧾 [DEBUG] Aplicando filtro de campos: {campos} - reporte_dinamico_views.py:211")
            datos_reporte = _filtrar_campos(datos_reporte, campos)


        # 5️⃣ Generar archivo según formato
        formato = parametros.get("formato", "pdf")
        print(f"🖨️ [DEBUG] Formato solicitado: {formato} - reporte_dinamico_views.py:217")

        # -------------------------------------------------------------------------
        # ✅ PDF
        if formato == "pdf":
            print("📄 [DEBUG] Generando archivo PDF... - reporte_dinamico_views.py:222")

            if tipo == "ventas":
                archivo_buffer = generar_reporte_ventas_pdf(datos_reporte, fecha_inicio, fecha_fin)
                nombre_archivo = f"reporte_ventas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                content_type = "application/pdf"

            elif tipo == "productos":
                archivo_buffer = generar_reporte_productos_pdf(datos_reporte)
                nombre_archivo = f"reporte_productos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                content_type = "application/pdf"

            elif tipo == "clientes":
                archivo_buffer = generar_reporte_clientes_pdf(datos_reporte)
                nombre_archivo = f"reporte_clientes_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                content_type = "application/pdf"

            elif tipo == "inventario":
                archivo_buffer = generar_reporte_inventario_pdf(datos_reporte)
                nombre_archivo = f"reporte_inventario_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                content_type = "application/pdf"

            elif tipo == "financiero":
                archivo_buffer = generar_reporte_financiero_pdf(
                    datos_reporte,
                    incluir_graficos=parametros.get("incluir_graficos", True),
                )
                nombre_archivo = f"reporte_financiero_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                content_type = "application/pdf"

            else:
                print(f"⚠️ [ERROR] Tipo '{tipo}' no soportado para PDF. - reporte_dinamico_views.py:253")
                return Response({'error': f"Tipo '{tipo}' no soportado para PDF."},
                                status=status.HTTP_400_BAD_REQUEST)

        # -------------------------------------------------------------------------
        # ✅ EXCEL
        elif formato == "excel":
            print("📊 [DEBUG] Generando archivo Excel... - reporte_dinamico_views.py:260")

            if tipo == "ventas":
                archivo_buffer = generar_reporte_ventas_excel(datos_reporte, fecha_inicio, fecha_fin)
                nombre_archivo = f"reporte_ventas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            elif tipo == "productos":
                archivo_buffer = generar_reporte_productos_excel(datos_reporte)
                nombre_archivo = f"reporte_productos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            elif tipo == "clientes":
                archivo_buffer = generar_reporte_clientes_excel(
                    datos_reporte,
                    incluir_graficos=parametros.get("incluir_graficos", True),
                )
                nombre_archivo = f"reporte_clientes_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            elif tipo == "inventario":
                archivo_buffer = generar_reporte_inventario_excel(
                    datos_reporte,
                    incluir_graficos=parametros.get("incluir_graficos", True),
                )
                nombre_archivo = f"reporte_inventario_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            elif tipo == "financiero":
                archivo_buffer = generar_reporte_financiero_excel(
                    datos_reporte,
                    incluir_graficos=parametros.get("incluir_graficos", True),
                )
                nombre_archivo = f"reporte_financiero_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            else:
                print(f"⚠️ [ERROR] Tipo '{tipo}' no soportado para Excel. - reporte_dinamico_views.py:297")
                return Response({'error': f"Tipo '{tipo}' no soportado para Excel."},
                                status=status.HTTP_400_BAD_REQUEST)

        # -------------------------------------------------------------------------
        # ✅ JSON (universal)
        elif formato == "json":
            print("🧩 [DEBUG] Generando archivo JSON... - reporte_dinamico_views.py:304")
            archivo_buffer = json.dumps(datos_reporte, indent=2, ensure_ascii=False).encode("utf-8")
            nombre_archivo = f"reporte_{tipo}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
            content_type = "application/json"

        else:
            print(f"⚠️ [ERROR] Formato no soportado: {formato} - reporte_dinamico_views.py:310")
            return Response({'error': 'Formato no soportado'},
                            status=status.HTTP_400_BAD_REQUEST)

        print(f"✅ [DEBUG] Archivo generado correctamente ({nombre_archivo}) - reporte_dinamico_views.py:314")


        # 6️⃣ Crear registro del reporte
        descripcion = parametros.get('descripcion', 'Reporte generado desde prompt')
        if es_voz:
            descripcion += ' (comando de voz)'
        if len(descripcion) > 100:
            descripcion = descripcion[:97] + "..."
        print(f"🧾 [DEBUG] Descripción final: {descripcion} - reporte_dinamico_views.py:323")

        # Convertir parámetros a tipos serializables
        parametros_serializables = {}
        for k, v in parametros.items():
            if isinstance(v, (list, dict)):
                parametros_serializables[k] = v
            elif hasattr(v, "isoformat"):
                parametros_serializables[k] = v.isoformat()
            else:
                parametros_serializables[k] = str(v)
        print(f"🧮 [DEBUG] Parámetros serializables preparados: {parametros_serializables} - reporte_dinamico_views.py:334")

        reporte = Reporte.objects.create(
            tipo=tipo,
            descripcion=descripcion,
            generado_por=request.user,
            formato=formato,
            parametros={
                'prompt_original': prompt,
                'es_voz': es_voz,
                **parametros_serializables
            },
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        print(f"✅ [DEBUG] Registro de Reporte creado: ID={reporte.id} - reporte_dinamico_views.py:349")

        # 7️⃣ Guardar archivo
        if isinstance(archivo_buffer, bytes):
            content = ContentFile(archivo_buffer)
        else:
            content = ContentFile(archivo_buffer.read())
        reporte.archivo.save(nombre_archivo, content, save=True)
        print("💾 [DEBUG] Archivo guardado en el modelo Reporte. - reporte_dinamico_views.py:357")

        # 8️⃣ Registrar en bitácora
        metodo = "comando de voz" if es_voz else "prompt de texto"
        Bitacora.objects.create(
            usuario=request.user,
            accion=f"Generó reporte dinámico de {tipo} mediante {metodo}: '{prompt[:50]}...'",
            ip=get_client_ip(request),
            estado=True
        )
        print("🪵 [DEBUG] Acción registrada en Bitácora correctamente. - reporte_dinamico_views.py:367")

        # 9️⃣ Serializar y responder
        serializer = ReporteSerializer(reporte, context={'request': request})
        print("📤 [DEBUG] Serialización completa. Preparando respuesta final. - reporte_dinamico_views.py:371")

        return Response({
            'mensaje': 'Reporte generado exitosamente desde prompt',
            'prompt_interpretado': parametros,
            'reporte': serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("💥 [ERROR] Excepción en generar_reporte_dinamico(): - reporte_dinamico_views.py:380")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error al generar reporte: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

###################################################################################################################################################################################
#########################################################################################################################################################################################33
##########################################################################################################################################################################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_reporte_por_voz(request):
    """
    Genera un reporte a partir de un comando de voz transcrito.
    """
    print("🎙️ [DEBUG] Entrando a generar_reporte_por_voz() - reporte_dinamico_views.py:397")

    texto_voz = request.data.get('texto_voz')
    print(f"📝 [DEBUG] Texto recibido de voz: {texto_voz} - reporte_dinamico_views.py:400")

    if not texto_voz:
        print("⚠️ [ERROR] No se proporcionó texto_voz en la solicitud. - reporte_dinamico_views.py:403")
        return Response(
            {'error': 'Debe proporcionar el texto transcrito de la voz'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Creamos un request simulado con autenticación y cabeceras copiadas
    from rest_framework.test import APIRequestFactory
    print("🏗️ [DEBUG] Creando instancia de APIRequestFactory()... - reporte_dinamico_views.py:411")
    factory = APIRequestFactory()

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    print(f"🔑 [DEBUG] Header de autorización original: {auth_header} - reporte_dinamico_views.py:415")

    fake_request = factory.post(
        '/api/reportes/generar-dinamico/',
        {
            'prompt': texto_voz,
            'es_voz': True
        },
        format='json',
        HTTP_AUTHORIZATION=auth_header
    )
    print("📨 [DEBUG] Request simulado creado correctamente. - reporte_dinamico_views.py:426")

    # ✅ Asignamos manualmente el usuario autenticado
    fake_request.user = request.user
    print(f"👤 [DEBUG] Usuario autenticado asignado: {request.user} - reporte_dinamico_views.py:430")

    # ✅ Llamamos al generador dinámico
    print("🚀 [DEBUG] Llamando a generar_reporte_dinamico(fake_request)... - reporte_dinamico_views.py:433")
    try:
        response = generar_reporte_dinamico(fake_request)
        print("✅ [DEBUG] generar_reporte_dinamico ejecutado correctamente. - reporte_dinamico_views.py:436")
        print(f"📦 [DEBUG] Tipo de respuesta: {type(response)} - reporte_dinamico_views.py:437")
        print(f"🧾 [DEBUG] Contenido de respuesta: {getattr(response, 'data', response)} - reporte_dinamico_views.py:438")
        return response
    except Exception as e:
        print("💥 [ERROR] Excepción al ejecutar generar_reporte_dinamico: - reporte_dinamico_views.py:441")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Ocurrió un error interno: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


##################################################################################################################################
################################################################################################################################
####################################################################################################################################
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
    print("🧠 [DEBUG] Entrando a interpretar_prompt_preview() - reporte_dinamico_views.py:478")

    prompt = request.data.get('prompt')
    print(f"📥 [DEBUG] Prompt recibido: {prompt} - reporte_dinamico_views.py:481")

    if not prompt:
        print("⚠️ [ERROR] No se proporcionó el campo 'prompt' en la solicitud. - reporte_dinamico_views.py:484")
        return Response(
            {'error': 'Debe proporcionar un prompt'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        print("🤖 [DEBUG] Llamando a interpretar_prompt() con IA activada (use_ai=True)... - reporte_dinamico_views.py:491")
        parametros = interpretar_prompt(prompt, use_ai=True)
        print(f"✅ [DEBUG] Parámetros interpretados correctamente: {parametros} - reporte_dinamico_views.py:493")

        # Generar mensaje de confirmación
        tipo = parametros.get('tipo', 'general')
        formato = parametros.get('formato', 'pdf')
        fecha_inicio = parametros.get('fecha_inicio')
        fecha_fin = parametros.get('fecha_fin')
        agrupar_por = parametros.get('agrupar_por')

        print(f"📊 [DEBUG] tipo={tipo}, formato={formato}, fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}, agrupar_por={agrupar_por} - reporte_dinamico_views.py:502")

        confirmacion = f"Se generará un reporte de {tipo}"

        if fecha_inicio and fecha_fin:
            try:
                confirmacion += f" del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"
                print(f"📆 [DEBUG] Rango de fechas formateado correctamente. - reporte_dinamico_views.py:509")
            except Exception as fe:
                print(f"⚠️ [WARN] Error al formatear fechas: {fe} - reporte_dinamico_views.py:511")

        if agrupar_por:
            confirmacion += f", agrupado por {agrupar_por}"
            print(f"📚 [DEBUG] Agrupamiento detectado: {agrupar_por} - reporte_dinamico_views.py:515")

        confirmacion += f" en formato {formato.upper()}"
        print(f"📝 [DEBUG] Mensaje de confirmación final: {confirmacion} - reporte_dinamico_views.py:518")

        # Convertir dates a strings para JSON
        parametros_json = {**parametros}
        if fecha_inicio:
            parametros_json['fecha_inicio'] = str(fecha_inicio)
        if fecha_fin:
            parametros_json['fecha_fin'] = str(fecha_fin)

        print(f"📦 [DEBUG] Parámetros listos para respuesta JSON: {parametros_json} - reporte_dinamico_views.py:527")

        return Response({
            'parametros_interpretados': parametros_json,
            'confirmacion': confirmacion
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print("💥 [ERROR] Excepción capturada al interpretar el prompt: - reporte_dinamico_views.py:535")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error al interpretar prompt: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    






##########################################################################################################################################
#########################################################################################################################################
##############################################################################################################################################
# Funciones auxiliares con depuración detallada

def _aplicar_agrupacion(datos_reporte, agrupar_por):
    """
    Agrupa los datos del reporte según el criterio especificado.
    
    Args:
        datos_reporte (dict): Datos del reporte
        agrupar_por (str): Campo por el cual agrupar
    
    Returns:
        dict: Datos agrupados
    """
    print("📊 [DEBUG] Entrando a _aplicar_agrupacion() - reporte_dinamico_views.py:565")
    print(f"➡️ [DEBUG] Criterio de agrupación recibido: {agrupar_por} - reporte_dinamico_views.py:566")
    print(f"📦 [DEBUG] Claves disponibles en datos_reporte: {list(datos_reporte.keys())} - reporte_dinamico_views.py:567")

    if 'ventas_detalle' not in datos_reporte:
        print("⚠️ [WARN] No existe 'ventas_detalle' en los datos, se devuelve sin modificar. - reporte_dinamico_views.py:570")
        return datos_reporte

    from collections import defaultdict
    ventas = datos_reporte['ventas_detalle']
    print(f"🧾 [DEBUG] Total de registros en ventas_detalle: {len(ventas)} - reporte_dinamico_views.py:575")

    grupos = defaultdict(lambda: {'total': 0, 'cantidad': 0, 'ventas': []})

    if agrupar_por == 'producto':
        print("🧩 [DEBUG] Agrupación por producto aún no implementada (passthrough). - reporte_dinamico_views.py:580")
        pass

    elif agrupar_por == 'cliente':
        print("👥 [DEBUG] Iniciando agrupación por cliente... - reporte_dinamico_views.py:584")
        for i, venta in enumerate(ventas, start=1):
            cliente = venta.get('usuario', 'Desconocido')
            total = venta.get('total', 0)
            print(f"🔹 [DEBUG] Procesando venta #{i}  Cliente: {cliente}, Total: {total} - reporte_dinamico_views.py:588")

            grupos[cliente]['total'] += total
            grupos[cliente]['cantidad'] += 1
            grupos[cliente]['ventas'].append(venta)

        datos_reporte['ventas_por_cliente'] = dict(grupos)
        print(f"✅ [DEBUG] Agrupación por cliente completada. Total de grupos: {len(grupos)} - reporte_dinamico_views.py:595")
        print(f"📘 [DEBUG] Ejemplo de grupo: {list(grupos.items())[:1]} - reporte_dinamico_views.py:596")

    else:
        print(f"⚠️ [WARN] Tipo de agrupación '{agrupar_por}' no reconocido. No se aplica agrupación. - reporte_dinamico_views.py:599")

    print("📤 [DEBUG] Saliendo de _aplicar_agrupacion() - reporte_dinamico_views.py:601")
    return datos_reporte

############################################################################################################################################
##########################################################################################################################################
############################################################################################################################################

def _filtrar_campos(datos_reporte, campos):
    """
    Filtra los campos del reporte según lo solicitado.
    
    Args:
        datos_reporte (dict): Datos del reporte
        campos (list): Lista de campos a incluir
    
    Returns:
        dict: Datos filtrados
    """
    print("📋 [DEBUG] Entrando a _filtrar_campos() - reporte_dinamico_views.py:619")
    print(f"➡️ [DEBUG] Campos solicitados para incluir: {campos} - reporte_dinamico_views.py:620")

    if 'ventas_detalle' not in datos_reporte:
        print("⚠️ [WARN] No existe 'ventas_detalle' en los datos, se devuelve sin modificar. - reporte_dinamico_views.py:623")
        return datos_reporte

    ventas_filtradas = []
    ventas = datos_reporte['ventas_detalle']
    print(f"🧾 [DEBUG] Total de registros originales: {len(ventas)} - reporte_dinamico_views.py:628")

    for idx, venta in enumerate(ventas, start=1):
        venta_filtrada = {}
        print(f"🔹 [DEBUG] Procesando venta #{idx}: {venta} - reporte_dinamico_views.py:632")

        for campo in campos:
            if campo == 'nombre_cliente':
                venta_filtrada['cliente'] = venta.get('usuario')
                print(f"👤 [DEBUG] Campo 'nombre_cliente' → {venta_filtrada['cliente']} - reporte_dinamico_views.py:637")
            elif campo == 'cantidad_compras':
                venta_filtrada['cantidad_compras'] = 1  # Cada registro es una compra
                print(f"🧾 [DEBUG] Campo 'cantidad_compras' → 1 - reporte_dinamico_views.py:640")
            elif campo == 'monto_total':
                venta_filtrada['monto_total'] = venta.get('total')
                print(f"💰 [DEBUG] Campo 'monto_total' → {venta_filtrada['monto_total']} - reporte_dinamico_views.py:643")
            elif campo == 'fechas':
                venta_filtrada['fecha'] = venta.get('fecha')
                print(f"📅 [DEBUG] Campo 'fecha' → {venta_filtrada['fecha']} - reporte_dinamico_views.py:646")
            elif campo == 'producto':
                venta_filtrada['producto'] = venta.get('producto', 'N/A')
                print(f"📦 [DEBUG] Campo 'producto' → {venta_filtrada['producto']} - reporte_dinamico_views.py:649")
            else:
                print(f"⚠️ [WARN] Campo desconocido: {campo} - reporte_dinamico_views.py:651")

        ventas_filtradas.append(venta_filtrada)

    datos_reporte['ventas_detalle'] = ventas_filtradas
    print(f"✅ [DEBUG] Total de ventas después del filtrado: {len(ventas_filtradas)} - reporte_dinamico_views.py:656")
    print(f"📘 [DEBUG] Ejemplo de venta filtrada: {ventas_filtradas[:1]} - reporte_dinamico_views.py:657")
    print("📤 [DEBUG] Saliendo de _filtrar_campos() - reporte_dinamico_views.py:658")

    return datos_reporte
