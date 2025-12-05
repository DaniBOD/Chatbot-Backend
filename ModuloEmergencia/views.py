"""
Views para el módulo de emergencias
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
import uuid
import logging

from .models import Emergencia, ChatConversation, ChatMessage
from .serializers import (
    EmergenciaSerializer,
    ChatConversationSerializer,
    ChatConversationSimpleSerializer,
    ChatMessageSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    InitChatRequestSerializer,
    InitChatResponseSerializer
)
from .services.chatbot_service import get_chatbot_service

logger = logging.getLogger(__name__)


class EmergenciaPagination(PageNumberPagination):
    """
    Paginación personalizada para emergencias
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class EmergenciaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar emergencias
    
    list: Listar todas las emergencias
    retrieve: Obtener una emergencia específica
    create: Crear una nueva emergencia manualmente
    update: Actualizar una emergencia
    partial_update: Actualizar parcialmente una emergencia
    destroy: Eliminar una emergencia
    """
    queryset = Emergencia.objects.all()
    serializer_class = EmergenciaSerializer
    pagination_class = EmergenciaPagination
    
    def get_queryset(self):
        """
        Permite filtrar emergencias por estado, sector, prioridad
        """
        queryset = Emergencia.objects.all()
        
        # Filtros opcionales
        estado = self.request.query_params.get('estado', None)
        sector = self.request.query_params.get('sector', None)
        prioridad = self.request.query_params.get('prioridad', None)
        
        if estado:
            queryset = queryset.filter(estado_emergencia=estado)
        if sector:
            queryset = queryset.filter(sector=sector)
        if prioridad:
            queryset = queryset.filter(nivel_prioridad=prioridad)
        
        return queryset.order_by('-fecha_creacion')
    
    @action(detail=True, methods=['post'])
    def calcular_prioridad(self, request, pk=None):
        """
        Recalcula la prioridad de una emergencia
        
        POST /api/emergencias/{id}/calcular_prioridad/
        """
        emergencia = self.get_object()
        emergencia.calcular_prioridad()
        emergencia.save()
        
        serializer = self.get_serializer(emergencia)
        return Response({
            'message': 'Prioridad recalculada',
            'emergencia': serializer.data
        })
    
    @action(detail=True, methods=['patch'])
    def actualizar_estado(self, request, pk=None):
        """
        Actualiza el estado de una emergencia
        
        PATCH /api/emergencias/{id}/actualizar_estado/
        Body: {"estado": "en_proceso"}
        """
        emergencia = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if not nuevo_estado:
            return Response(
                {'error': 'Estado requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el estado existe
        estados_validos = [choice[0] for choice in Emergencia.ESTADOS]
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Opciones: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        emergencia.estado_emergencia = nuevo_estado
        emergencia.save()
        
        serializer = self.get_serializer(emergencia)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de emergencias
        
        GET /api/emergencias/estadisticas/
        """
        from django.db.models import Count
        
        total = Emergencia.objects.count()
        por_estado = Emergencia.objects.values('estado_emergencia').annotate(
            count=Count('id_emergencia')
        )
        por_prioridad = Emergencia.objects.values('nivel_prioridad').annotate(
            count=Count('id_emergencia')
        )
        por_sector = Emergencia.objects.values('sector').annotate(
            count=Count('id_emergencia')
        )
        
        return Response({
            'total': total,
            'por_estado': list(por_estado),
            'por_prioridad': list(por_prioridad),
            'por_sector': list(por_sector)
        })


class ChatConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para conversaciones de chat
    
    list: Listar todas las conversaciones
    retrieve: Obtener una conversación específica con mensajes
    """
    queryset = ChatConversation.objects.all()
    serializer_class = ChatConversationSerializer
    lookup_field = 'session_id'
    
    def get_serializer_class(self):
        """
        Usa serializer simple para list, completo para retrieve
        """
        if self.action == 'list':
            return ChatConversationSimpleSerializer
        return ChatConversationSerializer
    
    @action(detail=True, methods=['get'])
    def mensajes(self, request, session_id=None):
        """
        Obtiene solo los mensajes de una conversación
        
        GET /api/emergencias/conversaciones/{session_id}/mensajes/
        """
        conversation = self.get_object()
        mensajes = conversation.mensajes.all().order_by('timestamp')
        serializer = ChatMessageSerializer(mensajes, many=True)
        
        return Response({
            'session_id': session_id,
            'estado': conversation.estado,
            'mensajes': serializer.data
        })


@api_view(['POST'])
def init_chat(request):
    """
    Inicia una nueva conversación de chat
    
    POST /api/emergencias/chat/init/
    Body: {"session_id": "opcional-uuid"}
    
    Response:
    {
        "session_id": "uuid",
        "message": "Mensaje inicial del bot",
        "estado": "iniciada"
    }
    """
    serializer = InitChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Generar session_id si no se proporciona
    session_id = serializer.validated_data.get('session_id') or str(uuid.uuid4())
    
    try:
        # Verificar si ya existe la sesión
        existing = ChatConversation.objects.filter(session_id=session_id).first()
        if existing:
            return Response(
                {'error': 'Sesión ya existe', 'session_id': session_id},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Iniciar conversación
        chatbot_service = get_chatbot_service()
        conversation, initial_message = chatbot_service.start_conversation(session_id)
        
        response_data = {
            'session_id': session_id,
            'message': initial_message,
            'estado': conversation.estado
        }
        
        response_serializer = InitChatResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error iniciando chat: {e}")
        return Response(
            {'error': 'Error al iniciar chat', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def chat_message(request):
    """
    Envía un mensaje en una conversación existente
    
    POST /api/emergencias/chat/message/
    Body: {
        "session_id": "uuid",
        "message": "texto del usuario"
    }
    
    Response:
    {
        "message": "respuesta del bot",
        "estado": "recolectando_datos",
        "session_id": "uuid",
        "completed": false,
        "datos_recolectados": ["sector", "nombre_usuario"],
        "datos_faltantes": ["telefono", "direccion"],
        ...
    }
    """
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    session_id = serializer.validated_data['session_id']
    user_message = serializer.validated_data['message']
    
    try:
        # Procesar mensaje
        chatbot_service = get_chatbot_service()
        response_data = chatbot_service.process_message(session_id, user_message)
        
        # Agregar session_id a la respuesta
        response_data['session_id'] = session_id
        
        # Validar y retornar
        response_serializer = ChatResponseSerializer(response_data)
        return Response(response_serializer.data)
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        return Response(
            {'error': 'Error al procesar mensaje', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def chat_status(request, session_id):
    """
    Obtiene el estado actual de una conversación
    
    GET /api/emergencias/chat/status/{session_id}/
    
    Response:
    {
        "session_id": "uuid",
        "estado": "recolectando_datos",
        "datos_recolectados": {...},
        "emergencia_id": "uuid" o null
    }
    """
    try:
        conversation = get_object_or_404(ChatConversation, session_id=session_id)
        serializer = ChatConversationSimpleSerializer(conversation)
        
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        return Response(
            {'error': 'Error al obtener estado'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def rag_stats(request):
    """
    Obtiene estadísticas del sistema RAG
    
    GET /api/emergencias/rag/stats/
    
    Response:
    {
        "collection_name": "emergencias_knowledge_base",
        "document_count": 42,
        "embedding_model": "..."
    }
    """
    try:
        from .RAG.retriever import get_rag_retriever
        from .RAG.embeddings import get_embeddings_manager
        
        rag_retriever = get_rag_retriever()
        embeddings_manager = get_embeddings_manager()
        
        collection_info = rag_retriever.get_collection_stats()
        embedding_info = embeddings_manager.get_model_info()
        
        return Response({
            **collection_info,
            **embedding_info
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo stats RAG: {e}")
        return Response(
            {'error': 'Error al obtener estadísticas'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
