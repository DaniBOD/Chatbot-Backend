"""
Serializers para el módulo de emergencias
"""
from rest_framework import serializers
from .models import Emergencia, ChatConversation, ChatMessage


class EmergenciaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Emergencia
    """
    tipo_emergencia_display = serializers.CharField(
        source='get_tipo_emergencia_display',
        read_only=True
    )
    sector_display = serializers.CharField(
        source='get_sector_display',
        read_only=True
    )
    estado_display = serializers.CharField(
        source='get_estado_emergencia_display',
        read_only=True
    )
    nivel_prioridad_display = serializers.CharField(
        source='get_nivel_prioridad_display',
        read_only=True
    )
    
    class Meta:
        model = Emergencia
        fields = [
            'id_emergencia',
            'nombre_usuario',
            'telefono',
            'sector',
            'sector_display',
            'direccion',
            'descripcion',
            'tipo_emergencia',
            'tipo_emergencia_display',
            'medidor_corriendo',
            'cantidad_agua',
            'fotografia',
            'estado_emergencia',
            'estado_display',
            'nivel_prioridad',
            'nivel_prioridad_display',
            'solicita_contacto_colaborativo',
            'fecha_creacion',
            'fecha_actualizacion',
            'notas_internas'
        ]
        read_only_fields = [
            'id_emergencia',
            'fecha_creacion',
            'fecha_actualizacion'
        ]


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
    """
    mensajes = ChatMessageSerializer(many=True, read_only=True)
    emergencia_id = serializers.UUIDField(
        source='emergencia.id_emergencia',
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
            'emergencia_id',
            'fecha_inicio',
            'fecha_fin',
            'mensajes'
        ]
        read_only_fields = ['id', 'fecha_inicio', 'fecha_fin']


class ChatConversationSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer simple para conversaciones (sin mensajes)
    """
    emergencia_id = serializers.UUIDField(
        source='emergencia.id_emergencia',
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
            'emergencia_id',
            'fecha_inicio',
            'fecha_fin'
        ]
        read_only_fields = ['id', 'fecha_inicio', 'fecha_fin']


class ChatRequestSerializer(serializers.Serializer):
    """
    Serializer para requests de chat
    """
    session_id = serializers.CharField(max_length=100, required=True)
    message = serializers.CharField(required=True, allow_blank=False)


class ChatResponseSerializer(serializers.Serializer):
    """
    Serializer para responses de chat
    """
    message = serializers.CharField()
    estado = serializers.CharField()
    session_id = serializers.CharField()
    completed = serializers.BooleanField(default=False)
    emergencia_id = serializers.UUIDField(required=False, allow_null=True)
    nivel_prioridad = serializers.CharField(required=False, allow_null=True)
    datos_recolectados = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    datos_faltantes = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class InitChatRequestSerializer(serializers.Serializer):
    """
    Serializer para iniciar chat
    """
    session_id = serializers.CharField(max_length=100, required=False)


class InitChatResponseSerializer(serializers.Serializer):
    """
    Serializer para response de inicio de chat
    """
    session_id = serializers.CharField()
    message = serializers.CharField()
    estado = serializers.CharField()
