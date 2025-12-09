"""
Serializers para el módulo de boletas
"""
from rest_framework import serializers
from .models import Boleta, ChatConversation, ChatMessage


class BoletaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Boleta
    """
    estado_pago_display = serializers.CharField(
        source='get_estado_pago_display',
        read_only=True
    )
    consumo_promedio_diario = serializers.SerializerMethodField()
    esta_vencida = serializers.SerializerMethodField()
    
    class Meta:
        model = Boleta
        fields = [
            'id_boleta',
            'nombre',
            'rut',
            'direccion',
            'fecha_emision',
            'periodo_facturacion',
            'consumo',
            'monto',
            'lectura_anterior',
            'lectura_actual',
            'fecha_vencimiento',
            'estado_pago',
            'estado_pago_display',
            'imagen_boleta',
            'fecha_creacion',
            'fecha_actualizacion',
            'notas',
            'consumo_promedio_diario',
            'esta_vencida'
        ]
        read_only_fields = [
            'id_boleta',
            'fecha_creacion',
            'fecha_actualizacion',
            'consumo_promedio_diario',
            'esta_vencida'
        ]
    
    def get_consumo_promedio_diario(self, obj):
        """
        Retorna el consumo promedio diario
        """
        return obj.get_consumo_promedio_diario()
    
    def get_esta_vencida(self, obj):
        """
        Retorna si la boleta está vencida
        """
        return obj.esta_vencida()


class BoletaSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer simple para Boleta (sin campos calculados)
    Útil para listados y relaciones
    """
    estado_pago_display = serializers.CharField(
        source='get_estado_pago_display',
        read_only=True
    )
    
    class Meta:
        model = Boleta
        fields = [
            'id_boleta',
            'nombre',
            'rut',
            'periodo_facturacion',
            'fecha_emision',
            'consumo',
            'monto',
            'estado_pago',
            'estado_pago_display'
        ]
        read_only_fields = ['id_boleta']


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer para mensajes de chat
    """
    
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'rol',
            'contenido',
            'timestamp',
            'metadata'
        ]
        read_only_fields = ['id', 'timestamp']


class ChatConversationSerializer(serializers.ModelSerializer):
    """
    Serializer para conversaciones de chat
    Incluye todos los mensajes de la conversación
    """
    mensajes = ChatMessageSerializer(many=True, read_only=True)
    boleta_principal_id = serializers.UUIDField(
        source='boleta_principal.id_boleta',
        read_only=True,
        allow_null=True
    )
    boleta_principal_data = BoletaSimpleSerializer(
        source='boleta_principal',
        read_only=True
    )
    boletas_comparadas_data = BoletaSimpleSerializer(
        source='boletas_comparadas',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = ChatConversation
        fields = [
            'id',
            'session_id',
            'estado',
            'datos_recolectados',
            'boleta_principal_id',
            'boleta_principal_data',
            'es_consulta_comparativa',
            'boletas_comparadas_data',
            'fecha_inicio',
            'fecha_fin',
            'metadata',
            'mensajes'
        ]
        read_only_fields = ['id', 'fecha_inicio', 'fecha_fin']


class ChatConversationSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer simple para conversaciones (sin mensajes ni detalles de boletas)
    Útil para listados
    """
    boleta_principal_id = serializers.UUIDField(
        source='boleta_principal.id_boleta',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ChatConversation
        fields = [
            'id',
            'session_id',
            'estado',
            'datos_recolectados',
            'boleta_principal_id',
            'es_consulta_comparativa',
            'fecha_inicio',
            'fecha_fin',
            'metadata'
        ]
        read_only_fields = ['id', 'fecha_inicio', 'fecha_fin']


class ChatRequestSerializer(serializers.Serializer):
    """
    Serializer para requests de chat
    Valida los mensajes entrantes del usuario
    """
    session_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='ID único de la sesión de chat (opcional; se generará si no se proporciona)'
    )
    message = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text='Mensaje del usuario'
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text='Metadatos adicionales del mensaje'
    )


class ChatResponseSerializer(serializers.Serializer):
    """
    Serializer para responses de chat
    Estructura la respuesta del asistente
    """
    message = serializers.CharField(
        help_text='Mensaje de respuesta del asistente'
    )
    estado = serializers.CharField(
        help_text='Estado actual de la conversación'
    )
    session_id = serializers.CharField(
        help_text='ID de la sesión'
    )
    completed = serializers.BooleanField(
        default=False,
        help_text='Indica si la conversación ha finalizado'
    )
    boleta_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='ID de la boleta consultada'
    )
    boleta_data = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text='Datos de la boleta consultada'
    )
    es_consulta_comparativa = serializers.BooleanField(
        default=False,
        help_text='Indica si es una consulta comparativa'
    )
    boletas_comparadas = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text='IDs de las boletas comparadas'
    )
    datos_recolectados = serializers.JSONField(
        required=False,
        help_text='Datos recolectados durante la conversación'
    )


class InitChatRequestSerializer(serializers.Serializer):
    """
    Serializer para iniciar una nueva conversación de chat
    """
    session_id = serializers.CharField(
        max_length=100,
        required=False,
        help_text='ID de sesión (opcional, se genera automáticamente si no se proporciona)'
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text='Metadatos iniciales de la conversación'
    )


class InitChatResponseSerializer(serializers.Serializer):
    """
    Serializer para response de inicio de chat
    """
    session_id = serializers.CharField(
        help_text='ID único de la sesión creada'
    )
    message = serializers.CharField(
        help_text='Mensaje de bienvenida del asistente'
    )
    estado = serializers.CharField(
        help_text='Estado inicial de la conversación'
    )


class BoletaConsultaSerializer(serializers.Serializer):
    """
    Serializer para consultar boletas por RUT o período
    """
    rut = serializers.CharField(
        max_length=12,
        required=False,
        allow_blank=True,
        help_text='RUT del cliente en formato XX.XXX.XXX-X'
    )
    periodo_facturacion = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text='Período de facturación (ejemplo: 2025-11)'
    )
    # Alias para frontend que may send `periodo`
    periodo = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text='Alias: periodo (mapeado a periodo_facturacion)'
    )
    fecha_inicio = serializers.DateField(
        required=False,
        help_text='Fecha de inicio del rango de consulta'
    )
    fecha_fin = serializers.DateField(
        required=False,
        help_text='Fecha de fin del rango de consulta'
    )
    estado_pago = serializers.CharField(
        max_length=20,
        required=False,
        help_text='Filtrar por estado de pago (ej: pendiente, pagada)'
    )
    solo_vigente = serializers.BooleanField(
        required=False,
        help_text='Si true, devuelve únicamente la boleta vigente para pagar (la más reciente pendiente)'
    )
    # Soportar búsqueda por nombre completo (frontend usa nombreCompleto)
    nombre = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text='Nombre completo del titular (búsqueda parcial)'
    )
    nombreCompleto = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text='Alias para nombre completo (acepta camelCase enviado por frontend)'
    )
    
    def validate(self, data):
        """
        Valida que al menos un criterio de búsqueda esté presente
        """
        # If frontend sent `periodo`, map it to `periodo_facturacion`
        if 'periodo' in data and 'periodo_facturacion' not in data:
            data['periodo_facturacion'] = data.get('periodo')

        # Normalize rut (strip spaces)
        if data.get('rut') and isinstance(data.get('rut'), str):
            data['rut'] = data['rut'].strip()
        # Normalize names: strip whitespace
        if data.get('nombre') and isinstance(data.get('nombre'), str):
            data['nombre'] = data['nombre'].strip()
        if data.get('nombreCompleto') and isinstance(data.get('nombreCompleto'), str):
            data['nombreCompleto'] = data['nombreCompleto'].strip()

        if not any([
            data.get('rut'),
            data.get('periodo_facturacion'),
            data.get('fecha_inicio'),
            data.get('estado_pago'),
            data.get('solo_vigente'),
            data.get('nombre'),
            data.get('nombreCompleto')
        ]):
            raise serializers.ValidationError(
                'Debe proporcionar al menos un criterio de búsqueda: rut, periodo_facturacion o fecha_inicio'
            )
        
        # Si se proporciona fecha_inicio, debe existir fecha_fin
        if data.get('fecha_inicio') and not data.get('fecha_fin'):
            raise serializers.ValidationError(
                'Si proporciona fecha_inicio, debe proporcionar también fecha_fin'
            )

        # Si se solicita solo_vigente debe indicar algún identificador (rut o nombre)
        if data.get('solo_vigente') and not any([data.get('rut'), data.get('nombre'), data.get('nombreCompleto')]):
            raise serializers.ValidationError(
                'Para pedir solo_vigente debe indicar el campo rut o un nombre (nombre o nombreCompleto)'
            )

        
        # Validar que fecha_fin sea posterior a fecha_inicio
        if data.get('fecha_inicio') and data.get('fecha_fin'):
            if data['fecha_fin'] < data['fecha_inicio']:
                raise serializers.ValidationError(
                    'fecha_fin debe ser posterior a fecha_inicio'
                )
        
        return data
