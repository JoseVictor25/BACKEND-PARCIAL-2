"""
Parser de prompts para generación dinámica de reportes.
Combina reglas clásicas + interpretación IA (Gemini/GPT).
"""
import re
from datetime import datetime
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from django.conf import settings  # ✅ Importa configuración de Django

# 🔹 Solo se usa si tienes una clave de Gemini o GPT configurada en entorno
try:
    import google.generativeai as genai
    import os
    GEMINI_KEY = getattr(settings, "GEMINI_API_KEY", None)
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        print("🔑 [DEBUG] Clave GEMINI detectada y configurada correctamente. - reporte_prompt_parser.py:18")
    else:
        print("⚠️ [WARN] No se encontró GEMINI_API_KEY en entorno. - reporte_prompt_parser.py:20")
except ImportError:
    genai = None
    print("⚠️ [WARN] Librería google.generativeai no instalada. - reporte_prompt_parser.py:23")


class ReportePromptParser:
    MESES = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10,
        'noviembre': 11, 'diciembre': 12
    }

    TIPOS_REPORTE = {
        'venta': 'ventas', 'ventas': 'ventas',
        'producto': 'productos', 'productos': 'productos',
        'cliente': 'clientes', 'clientes': 'clientes',
        'inventario': 'inventario', 'stock': 'inventario',
        'financiero': 'financiero', 'finanzas': 'financiero'
    }

    FORMATOS = {'pdf': 'pdf', 'excel': 'excel', 'xlsx': 'excel', 'json': 'json'}

    AGRUPACIONES = {
        'producto': 'producto', 'productos': 'producto',
        'cliente': 'cliente', 'clientes': 'cliente',
        'categoria': 'categoria', 'categoría': 'categoria',
        'marca': 'marca', 'día': 'dia', 'dia': 'dia',
        'mes': 'mes', 'año': 'anio', 'semana': 'semana'
    }

    def __init__(self, prompt, use_ai=False):
        self.prompt = prompt.lower()
        self.parametros = {}
        self.use_ai = use_ai
        print(f"🧠 [DEBUG] Inicializando parser con prompt: '{self.prompt}' | use_ai={self.use_ai} - reporte_prompt_parser.py:55")

    # ------------------------------------------------------------------ #
    def parse(self):
        """Intenta primero con reglas, luego IA si use_ai=True."""
        print("🔍 [DEBUG] Iniciando análisis del prompt... - reporte_prompt_parser.py:60")
        try:
            self._extraer_tipo_reporte()
            self._extraer_formato()
            self._extraer_fechas()
            self._extraer_agrupacion()
            self._extraer_campos()
            self._generar_descripcion()
        except Exception as e:
            print("⚠️ [ERROR] Error en parser de reglas > - reporte_prompt_parser.py:69", e)

        # Si falta algo esencial y hay IA disponible
        if self.use_ai and (not self.parametros.get("tipo") or not self.parametros.get("formato")):
            print("🤖 [DEBUG] Activando interpretación IA por datos faltantes... - reporte_prompt_parser.py:73")
            ia_result = self._interpretar_con_ia(self.prompt)
            if ia_result:
                print(f"✅ [DEBUG] IA devolvió: {ia_result} - reporte_prompt_parser.py:76")
                self.parametros.update(ia_result)
            else:
                print("⚠️ [WARN] IA no devolvió resultados válidos. - reporte_prompt_parser.py:79")

        print(f"📦 [DEBUG] Resultado final del parser: {self.parametros} - reporte_prompt_parser.py:81")
        return self.parametros

    # ------------------------------------------------------------------ #
    def _extraer_tipo_reporte(self):
        print("🧾 [DEBUG] Buscando tipo de reporte... - reporte_prompt_parser.py:86")

        # 🧩 Priorizar palabras más largas (evita confundir "venta" dentro de "inventario")
        TIPOS_ORDENADOS = sorted(self.TIPOS_REPORTE.items(), key=lambda x: len(x[0]), reverse=True)

        for palabra, tipo in TIPOS_ORDENADOS:
            # Buscar palabra completa (no subcadena)
            if re.search(rf'\b{re.escape(palabra)}\b', self.prompt):
                self.parametros['tipo'] = tipo
                print(f"✅ [DEBUG] Tipo de reporte detectado: {tipo} - reporte_prompt_parser.py:95")
                return

        # Si no se encontró nada, asignar "ventas" por defecto
        self.parametros['tipo'] = 'ventas'
        print("⚠️ [WARN] No se detectó tipo explícito, usando 'ventas' por defecto. - reporte_prompt_parser.py:100")





    def _extraer_formato(self):
        print("📄 [DEBUG] Buscando formato de salida... - reporte_prompt_parser.py:107")
        for palabra, formato in self.FORMATOS.items():
            if palabra in self.prompt:
                self.parametros['formato'] = formato
                print(f"✅ [DEBUG] Formato detectado: {formato} - reporte_prompt_parser.py:111")
                return
        self.parametros['formato'] = 'pdf'
        print("⚠️ [WARN] No se especificó formato, usando 'pdf' por defecto. - reporte_prompt_parser.py:114")





    def _extraer_fechas(self):
        print("📅 [DEBUG] Intentando detectar fechas... - reporte_prompt_parser.py:121")

        # 🧩 1️⃣ Detección de rango de meses con años distintos (ej: "enero de 2020 a marzo de 2023")
        rango_meses = re.search(
            r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\s*(?:de)?\s*(20\d{2})?.*?(?:hasta|a|-|al)\s*(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\s*(?:de)?\s*(20\d{2})?",
            self.prompt
        )
        if rango_meses:
            try:
                mes_inicio, año_inicio, mes_fin, año_fin = rango_meses.groups()
                año_inicio = int(año_inicio) if año_inicio else datetime.now().year
                año_fin = int(año_fin) if año_fin else año_inicio

                fecha_inicio = datetime(año_inicio, self.MESES[mes_inicio], 1)
                fecha_fin = datetime(año_fin, self.MESES[mes_fin], 1) + relativedelta(months=1, days=-1)

                self.parametros.update({
                    'fecha_inicio': fecha_inicio.date(),
                    'fecha_fin': fecha_fin.date()
                })
                print(f"✅ [DEBUG] Fechas detectadas por rango de meses: {fecha_inicio.date()} → {fecha_fin.date()} - reporte_prompt_parser.py:141")
                return
            except Exception as e:
                print("⚠️ [WARN] Error al procesar rango de meses: - reporte_prompt_parser.py:144", e)

        # 🧩 2️⃣ Detección de un solo mes con posible año
        for mes_nombre, mes_num in self.MESES.items():
            if mes_nombre in self.prompt:
                año_match = re.search(r'\b(20\d{2})\b', self.prompt)
                año = int(año_match.group(1)) if año_match else datetime.now().year
                fecha_inicio = datetime(año, mes_num, 1)
                fecha_fin = fecha_inicio + relativedelta(months=1, days=-1)

                self.parametros.update({
                    'fecha_inicio': fecha_inicio.date(),
                    'fecha_fin': fecha_fin.date()
                })
                print(f"✅ [DEBUG] Fechas detectadas por mes: {fecha_inicio.date()} → {fecha_fin.date()} - reporte_prompt_parser.py:158")
                return

        # 🧩 3️⃣ Detección manual con formato numérico (ej: 01/01/2023 - 30/06/2023)
        match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}).+?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', self.prompt)
        if match:
            try:
                fi, ff = date_parser.parse(match[1], dayfirst=True), date_parser.parse(match[2], dayfirst=True)
                self.parametros.update({'fecha_inicio': fi.date(), 'fecha_fin': ff.date()})
                print(f"✅ [DEBUG] Fechas detectadas manualmente: {fi.date()} → {ff.date()} - reporte_prompt_parser.py:167")
                return
            except Exception as e:
                print("⚠️ [WARN] Error parseando fechas manuales: - reporte_prompt_parser.py:170", e)

        # 🧩 4️⃣ Expresiones relativas
        hoy = datetime.now()
        if "último mes" in self.prompt or "mes pasado" in self.prompt:
            inicio = (hoy - relativedelta(months=1)).replace(day=1)
            fin = hoy.replace(day=1) - relativedelta(days=1)
            print("📆 [DEBUG] Intervalo: último mes - reporte_prompt_parser.py:177")
        elif "último trimestre" in self.prompt or "trimestre pasado" in self.prompt:
            inicio = hoy - relativedelta(months=3)
            inicio = datetime(inicio.year, inicio.month, 1)
            fin = hoy.replace(day=1) - relativedelta(days=1)
            print("📆 [DEBUG] Intervalo: último trimestre - reporte_prompt_parser.py:182")
        else:
            inicio = hoy.replace(day=1)
            fin = (inicio + relativedelta(months=1)) - relativedelta(days=1)
            print("📆 [DEBUG] Intervalo: mes actual (por defecto) - reporte_prompt_parser.py:186")

        self.parametros.update({'fecha_inicio': inicio.date(), 'fecha_fin': fin.date()})
        print(f"✅ [DEBUG] Fechas finales: {inicio.date()} → {fin.date()} - reporte_prompt_parser.py:189")

        def _extraer_agrupacion(self):
            print("📚 [DEBUG] Buscando criterio de agrupación... - reporte_prompt_parser.py:192")
            match = re.search(r'agrupado\s+por\s+(\w+)', self.prompt)
            if match:
                agru = match.group(1)
                for k, v in self.AGRUPACIONES.items():
                    if k in agru:
                        self.parametros['agrupar_por'] = v
                        print(f"✅ [DEBUG] Agrupación detectada: {v} - reporte_prompt_parser.py:199")
                        return
            if "por mes" in self.prompt:
                self.parametros['agrupar_por'] = "mes"
                print("✅ [DEBUG] Agrupación detectada: mes - reporte_prompt_parser.py:203")
            else:
                print("⚠️ [WARN] No se detectó agrupación. - reporte_prompt_parser.py:205")










    def _extraer_campos(self):
        print("📋 [DEBUG] Buscando campos a mostrar... - reporte_prompt_parser.py:217")
        match = re.search(r'mostrar\s+(.+?)(?:\.|$)', self.prompt)
        if not match:
            print("⚠️ [WARN] No se especificaron campos. - reporte_prompt_parser.py:220")
            return
        campos = [c.strip() for c in match.group(1).split(',')]
        campos_mapeados = []
        for campo in campos:
            if 'cliente' in campo: campos_mapeados.append('nombre_cliente')
            elif 'cantidad' in campo: campos_mapeados.append('cantidad_compras')
            elif 'monto' in campo or 'total' in campo: campos_mapeados.append('monto_total')
            elif 'fecha' in campo: campos_mapeados.append('fechas')
            elif 'producto' in campo: campos_mapeados.append('producto')
        self.parametros['campos'] = campos_mapeados
        print(f"✅ [DEBUG] Campos mapeados: {campos_mapeados} - reporte_prompt_parser.py:231")

    def _generar_descripcion(self):
        print("📝 [DEBUG] Generando descripción del reporte... - reporte_prompt_parser.py:234")
        t, f = self.parametros.get('tipo', 'general'), self.parametros.get('formato', 'pdf')
        fi, ff = self.parametros.get('fecha_inicio'), self.parametros.get('fecha_fin')
        desc = f"Reporte de {t}"
        if fi and ff: desc += f" del {fi.strftime('%d/%m/%Y')} al {ff.strftime('%d/%m/%Y')}"
        if self.parametros.get('agrupar_por'): desc += f", agrupado por {self.parametros['agrupar_por']}"
        desc += f" ({f.upper()})"
        self.parametros['descripcion'] = desc
        print(f"✅ [DEBUG] Descripción final: {desc} - reporte_prompt_parser.py:242")

    # ------------------------------------------------------------------ #
    def _interpretar_con_ia(self, prompt):
        """Usa Gemini o GPT para interpretar comandos complejos."""
        print("🤖 [DEBUG] Intentando interpretación IA con Gemini... - reporte_prompt_parser.py:247")
        if not genai or not GEMINI_KEY:
            print("⚠️ [WARN] Gemini no configurado, modo IA deshabilitado. - reporte_prompt_parser.py:249")
            return None
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            instruccion = (
                "Analiza el siguiente comando en español y devuelve un JSON plano "
                "con las claves: tipo, formato, fecha_inicio, fecha_fin, agrupar_por, incluir_graficos. "
                "Usa nombres compatibles con reportes empresariales (ventas, productos, clientes, inventario, financiero). "
                f"Comando: {prompt}"
            )
            print("📤 [DEBUG] Enviando instrucción al modelo Gemini... - reporte_prompt_parser.py:259")
            resp = model.generate_content(instruccion)
            import json
            resultado = json.loads(resp.text.strip("`\n "))
            print(f"✅ [DEBUG] Gemini devolvió resultado parseado: {resultado} - reporte_prompt_parser.py:263")
            return resultado
        except Exception as e:
            print("⚠️ [ERROR] Error interpretando con IA > - reporte_prompt_parser.py:266", e)
            return None


def interpretar_prompt(prompt, use_ai=False):
    """Función helper para usar dentro de views."""
    print(f"🧩 [DEBUG] interpretando prompt='{prompt}' | use_ai={use_ai} - reporte_prompt_parser.py:272")
    return ReportePromptParser(prompt, use_ai=use_ai).parse()
