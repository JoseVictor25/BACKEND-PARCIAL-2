"""
Parser de prompts para generación dinámica de reportes.
Interpreta comandos en lenguaje natural para construir reportes.
"""
import re
from datetime import datetime
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta


class ReportePromptParser:
    """
    Clase para interpretar prompts de texto y extraer parámetros
    para la generación de reportes.
    """
    
    # Patrones de meses en español
    MESES = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    
    # Tipos de reporte reconocidos
    TIPOS_REPORTE = {
        'venta': 'ventas',
        'ventas': 'ventas',
        'producto': 'productos',
        'productos': 'productos',
        'cliente': 'clientes',
        'clientes': 'clientes',
        'inventario': 'inventario',
        'stock': 'inventario',
        'financiero': 'financiero',
        'finanzas': 'financiero'
    }
    
    # Formatos reconocidos
    FORMATOS = {
        'pdf': 'pdf',
        'excel': 'excel',
        'xlsx': 'excel',
        'json': 'json'
    }
    
    # Agrupaciones comunes
    AGRUPACIONES = {
        'producto': 'producto',
        'productos': 'producto',
        'cliente': 'cliente',
        'clientes': 'cliente',
        'categoria': 'categoria',
        'categoría': 'categoria',
        'marca': 'marca',
        'día': 'dia',
        'dia': 'dia',
        'mes': 'mes',
        'año': 'anio',
        'semana': 'semana'
    }

    def __init__(self, prompt):
        """
        Inicializa el parser con un prompt.
        
        Args:
            prompt (str): Texto del comando a interpretar
        """
        self.prompt = prompt.lower()
        self.parametros = {}
    
    def parse(self):
        """
        Parsea el prompt y extrae los parámetros.
        
        Returns:
            dict: Diccionario con los parámetros extraídos
        """
        self._extraer_tipo_reporte()
        self._extraer_formato()
        self._extraer_fechas()
        self._extraer_agrupacion()
        self._extraer_campos()
        self._generar_descripcion()
        
        return self.parametros
    
    def _extraer_tipo_reporte(self):
        """Identifica el tipo de reporte solicitado."""
        for palabra, tipo in self.TIPOS_REPORTE.items():
            if palabra in self.prompt:
                self.parametros['tipo'] = tipo
                return
        
        # Por defecto, asumir reporte de ventas
        self.parametros['tipo'] = 'ventas'
    
    def _extraer_formato(self):
        """Identifica el formato del reporte."""
        for palabra, formato in self.FORMATOS.items():
            if palabra in self.prompt:
                self.parametros['formato'] = formato
                return
        
        # Por defecto, PDF
        self.parametros['formato'] = 'pdf'
    
    def _extraer_fechas(self):
        """
        Extrae rangos de fechas del prompt.
        Soporta varios formatos:
        - "del mes de septiembre"
        - "del 01/10/2024 al 01/01/2025"
        - "de octubre"
        - "del año 2024"
        """
        # Buscar mes específico
        for mes_nombre, mes_num in self.MESES.items():
            if mes_nombre in self.prompt:
                # Determinar el año (actual por defecto)
                año_match = re.search(r'\b(20\d{2})\b', self.prompt)
                año = int(año_match.group(1)) if año_match else datetime.now().year
                
                # Crear rango del mes completo
                fecha_inicio = datetime(año, mes_num, 1)
                if mes_num == 12:
                    fecha_fin = datetime(año + 1, 1, 1) - relativedelta(days=1)
                else:
                    fecha_fin = datetime(año, mes_num + 1, 1) - relativedelta(days=1)
                
                self.parametros['fecha_inicio'] = fecha_inicio.date()
                self.parametros['fecha_fin'] = fecha_fin.date()
                return
        
        # Buscar patrón "del DD/MM/YYYY al DD/MM/YYYY"
        fecha_pattern = r'del?\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+al?\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        match = re.search(fecha_pattern, self.prompt)
        
        if match:
            try:
                fecha_inicio_str = match.group(1)
                fecha_fin_str = match.group(2)
                
                # Parsear las fechas
                fecha_inicio = date_parser.parse(fecha_inicio_str, dayfirst=True)
                fecha_fin = date_parser.parse(fecha_fin_str, dayfirst=True)
                
                self.parametros['fecha_inicio'] = fecha_inicio.date()
                self.parametros['fecha_fin'] = fecha_fin.date()
                return
            except:
                pass
        
        # Buscar "del periodo" o "período"
        periodo_pattern = r'periodo\s+del?\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+al?\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        match = re.search(periodo_pattern, self.prompt)
        
        if match:
            try:
                fecha_inicio_str = match.group(1)
                fecha_fin_str = match.group(2)
                
                fecha_inicio = date_parser.parse(fecha_inicio_str, dayfirst=True)
                fecha_fin = date_parser.parse(fecha_fin_str, dayfirst=True)
                
                self.parametros['fecha_inicio'] = fecha_inicio.date()
                self.parametros['fecha_fin'] = fecha_fin.date()
                return
            except:
                pass
        
        # Si no se especifica, usar el mes actual
        hoy = datetime.now()
        primer_dia_mes = datetime(hoy.year, hoy.month, 1)
        if hoy.month == 12:
            ultimo_dia_mes = datetime(hoy.year + 1, 1, 1) - relativedelta(days=1)
        else:
            ultimo_dia_mes = datetime(hoy.year, hoy.month + 1, 1) - relativedelta(days=1)
        
        self.parametros['fecha_inicio'] = primer_dia_mes.date()
        self.parametros['fecha_fin'] = ultimo_dia_mes.date()
    
    def _extraer_agrupacion(self):
        """Identifica si se solicita agrupar los datos."""
        # Buscar "agrupado por X"
        agrupado_pattern = r'agrupado\s+por\s+(\w+)'
        match = re.search(agrupado_pattern, self.prompt)
        
        if match:
            agrupacion_texto = match.group(1)
            for palabra, agrupacion in self.AGRUPACIONES.items():
                if palabra in agrupacion_texto:
                    self.parametros['agrupar_por'] = agrupacion
                    return
        
        self.parametros['agrupar_por'] = None
    
    def _extraer_campos(self):
        """
        Extrae los campos específicos que el usuario quiere ver.
        Busca frases como "debe mostrar X, Y, Z"
        """
        campos_pattern = r'debe\s+mostrar\s+(.+?)(?:\.|$)'
        match = re.search(campos_pattern, self.prompt)
        
        if match:
            campos_texto = match.group(1)
            # Dividir por comas y limpiar
            campos = [c.strip() for c in campos_texto.split(',')]
            
            # Mapear campos a nombres de columnas
            campos_mapeados = []
            for campo in campos:
                if 'nombre' in campo and 'cliente' in campo:
                    campos_mapeados.append('nombre_cliente')
                elif 'cantidad' in campo and 'compra' in campo:
                    campos_mapeados.append('cantidad_compras')
                elif 'monto' in campo or 'total' in campo:
                    campos_mapeados.append('monto_total')
                elif 'fecha' in campo:
                    campos_mapeados.append('fechas')
                elif 'producto' in campo:
                    campos_mapeados.append('producto')
            
            self.parametros['campos'] = campos_mapeados
        else:
            self.parametros['campos'] = None
    
    def _generar_descripcion(self):
        """Genera una descripción legible del reporte."""
        tipo = self.parametros.get('tipo', 'general')
        formato = self.parametros.get('formato', 'pdf')
        fecha_inicio = self.parametros.get('fecha_inicio')
        fecha_fin = self.parametros.get('fecha_fin')
        
        descripcion = f"Reporte de {tipo}"
        
        if fecha_inicio and fecha_fin:
            descripcion += f" del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"
        
        if self.parametros.get('agrupar_por'):
            descripcion += f", agrupado por {self.parametros['agrupar_por']}"
        
        descripcion += f" (formato {formato.upper()})"
        
        self.parametros['descripcion'] = descripcion


def interpretar_prompt(prompt):
    """
    Función helper para interpretar un prompt y retornar parámetros.
    
    Args:
        prompt (str): Texto del comando
    
    Returns:
        dict: Parámetros extraídos
    
    Ejemplo:
        >>> params = interpretar_prompt("Quiero un reporte de ventas de septiembre en PDF")
        >>> print(params)
        {
            'tipo': 'ventas',
            'formato': 'pdf',
            'fecha_inicio': date(2025, 9, 1),
            'fecha_fin': date(2025, 9, 30),
            ...
        }
    """
    parser = ReportePromptParser(prompt)
    return parser.parse()


# Ejemplos de uso
if __name__ == "__main__":
    # Ejemplo 1
    prompt1 = "Quiero un reporte de ventas del mes de septiembre, agrupado por producto, en PDF."
    params1 = interpretar_prompt(prompt1)
    print("Ejemplo 1:", params1)
    
    # Ejemplo 2
    prompt2 = "Quiero un reporte en Excel que muestre las ventas del periodo del 01/10/2024 al 01/01/2025. Debe mostrar el nombre del cliente, la cantidad de compras que realizó, el monto total que pagó."
    params2 = interpretar_prompt(prompt2)
    print("Ejemplo 2:", params2)
    
    # Ejemplo 3
    prompt3 = "Muéstrame el inventario en PDF"
    params3 = interpretar_prompt(prompt3)
    print("Ejemplo 3:", params3)