from rest_framework import serializers
from .models import Reporte


class ReporteSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Reporte.
    """
    generado_por_username = serializers.CharField(
        source='generado_por.username',
        read_only=True
    )
    tipo_display = serializers.CharField(
        source='get_tipo_display',
        read_only=True
    )
    formato_display = serializers.CharField(
        source='get_formato_display',
        read_only=True
    )
    archivo_url = serializers.SerializerMethodField()

    class Meta:
        model = Reporte
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'descripcion',
            'fecha_generacion',
            'generado_por',
            'generado_por_username',
            'formato',
            'formato_display',
            'archivo',
            'archivo_url',
            'parametros',
            'fecha_inicio',
            'fecha_fin'
        ]
        read_only_fields = ['fecha_generacion', 'generado_por', 'archivo']

    def get_archivo_url(self, obj):
        """Retorna la URL del archivo si existe."""
        if obj.archivo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.archivo.url)
        return None


class ReporteCreateSerializer(serializers.Serializer):
    """
    Serializer para crear reportes con parámetros personalizados.
    """
    tipo = serializers.ChoiceField(choices=Reporte.TIPO_CHOICES)
    formato = serializers.ChoiceField(
        choices=Reporte.FORMATO_CHOICES,
        default='pdf'
    )
    fecha_inicio = serializers.DateField(required=False, allow_null=True)
    fecha_fin = serializers.DateField(required=False, allow_null=True)
    descripcion = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    # Parámetros adicionales opcionales
    incluir_graficos = serializers.BooleanField(default=True)
    agrupar_por = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Validaciones personalizadas."""
        if data.get('fecha_inicio') and data.get('fecha_fin'):
            if data['fecha_fin'] < data['fecha_inicio']:
                raise serializers.ValidationError(
                    "La fecha de fin no puede ser anterior a la fecha de inicio."
                )
        return data