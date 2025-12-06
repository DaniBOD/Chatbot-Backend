"""
Views para el módulo de boletas
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta
import uuid
import logging

from .models import Boleta, ChatConversation, ChatMessage
from .serializers import (
    BoletaSerializer,
    BoletaSimpleSerializer,
    ChatConversationSerializer,
    ChatConversationSimpleSerializer,
    ChatMessageSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    InitChatRequestSerializer,
    InitChatResponseSerializer,
    BoletaConsultaSerializer
)
from .services.chatbot_service import get_chatbot_service

logger = logging.getLogger(__name__)


class BoletaPagination(PageNumberPagination):
    """
    Paginación personalizada para boletas
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BoletaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar boletas
    
    list: Listar todas las boletas
    retrieve: Obtener una boleta específica
    create: Crear una nueva boleta manualmente
    update: Actualizar una boleta
    partial_update: Actualizar parcialmente una boleta
    destroy: Eliminar una boleta
    """
    queryset = Boleta.objects.all()
    serializer_class = BoletaSerializer
    pagination_class = BoletaPagination
    lookup_field = 'id_boleta'
    
    def get_queryset(self):
        """
        Permite filtrar boletas por estado de pago, RUT, período, rango de fechas
        """
        queryset = Boleta.objects.all()
        
        # Filtros opcionales
        estado_pago = self.request.query_params.get('estado_pago', None)
        rut = self.request.query_params.get('rut', None)
        periodo = self.request.query_params.get('periodo', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        vencidas = self.request.query_params.get('vencidas', None)
        
        if estado_pago:
            queryset = queryset.filter(estado_pago=estado_pago)
        if rut:
            queryset = queryset.filter(rut=rut)
        if periodo:
            queryset = queryset.filter(periodo_facturacion=periodo)
        if fecha_desde:
            queryset = queryset.filter(fecha_emision__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_emision__lte=fecha_hasta)
        if vencidas and vencidas.lower() == 'true':
            queryset = queryset.filter(fecha_vencimiento__lt=datetime.now().date(), estado_pago='pendiente')
        
        return queryset.order_by('-fecha_emision')
    
    def get_serializer_class(self):
        """
        Usa serializer simple para list, completo para retrieve/create/update
        """
        if self.action == 'list':
            return BoletaSimpleSerializer
        return BoletaSerializer
    
    @action(detail=False, methods=['post'])
    def consultar(self, request):
        """
        Consulta boletas con criterios múltiples
        
        POST /api/boletas/consultar/
        Body: {
            "rut": "12345678-9",
            "periodo": "2024-01",
            "fecha_inicio": "2024-01-01",
            "fecha_fin": "2024-12-31"
        }
        """
        serializer = BoletaConsultaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        queryset = Boleta.objects.all()
        
        # Aplicar filtros
        if 'rut' in data:
            queryset = queryset.filter(rut=data['rut'])
        if 'periodo' in data:
            queryset = queryset.filter(periodo_facturacion=data['periodo'])
        if 'fecha_inicio' in data:
            queryset = queryset.filter(fecha_emision__gte=data['fecha_inicio'])
        if 'fecha_fin' in data:
            queryset = queryset.filter(fecha_emision__lte=data['fecha_fin'])
        
        queryset = queryset.order_by('-fecha_emision')
        
        # Paginar resultados
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BoletaSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BoletaSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def calcular_consumo(self, request, id_boleta=None):
        """
        Calcula el consumo de una boleta basado en lecturas
        
        GET /api/boletas/{id_boleta}/calcular_consumo/
        """
        boleta = self.get_object()
        consumo = boleta.calcular_consumo()
        
        return Response({
            'id_boleta': str(boleta.id_boleta),
            'periodo': boleta.periodo_facturacion,
            'lecturas': boleta.lecturas,
            'consumo_calculado': consumo,
            'consumo_actual': boleta.consumo
        })
    
    @action(detail=False, methods=['get'])
    def por_rut(self, request):
        """
        Obtiene todas las boletas de un RUT específico
        
        GET /api/boletas/por_rut/?rut=12345678-9
        """
        rut = request.query_params.get('rut', None)
        
        if not rut:
            return Response(
                {'error': 'Parámetro rut requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        boletas = Boleta.objects.filter(rut=rut).order_by('-fecha_emision')
        
        # Paginar resultados
        page = self.paginate_queryset(boletas)
        if page is not None:
            serializer = BoletaSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BoletaSerializer(boletas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def comparar(self, request):
        """
        Compara múltiples boletas (por IDs o períodos de un RUT)
        
        POST /api/boletas/comparar/
        Body: {
            "boletas_ids": ["uuid1", "uuid2", "uuid3"]
        }
        o
        Body: {
            "rut": "12345678-9",
            "periodos": ["2024-01", "2024-02", "2024-03"]
        }
        """
        boletas_ids = request.data.get('boletas_ids', [])
        rut = request.data.get('rut')
        periodos = request.data.get('periodos', [])
        
        if boletas_ids:
            boletas = Boleta.objects.filter(id_boleta__in=boletas_ids)
        elif rut and periodos:
            boletas = Boleta.objects.filter(rut=rut, periodo_facturacion__in=periodos)
        else:
            return Response(
                {'error': 'Debe proporcionar boletas_ids o (rut + periodos)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not boletas.exists():
            return Response(
                {'error': 'No se encontraron boletas para comparar'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calcular estadísticas comparativas
        consumo_promedio = boletas.aggregate(Avg('consumo'))['consumo__avg']
        monto_promedio = boletas.aggregate(Avg('monto'))['monto__avg']
        consumo_total = boletas.aggregate(Sum('consumo'))['consumo__sum']
        monto_total = boletas.aggregate(Sum('monto'))['monto__sum']
        
        serializer = BoletaSerializer(boletas, many=True)
        
        return Response({
            'cantidad_boletas': boletas.count(),
            'boletas': serializer.data,
            'estadisticas': {
                'consumo_promedio': consumo_promedio,
                'monto_promedio': monto_promedio,
                'consumo_total': consumo_total,
                'monto_total': monto_total
            }
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas generales de boletas
        
        GET /api/boletas/estadisticas/
        Filtros opcionales: ?rut=12345678-9&fecha_desde=2024-01-01&fecha_hasta=2024-12-31
        """
        # Aplicar filtros opcionales
        queryset = self.get_queryset()
        
        total = queryset.count()
        por_estado_pago = queryset.values('estado_pago').annotate(
            count=Count('id_boleta')
        )
        
        # Estadísticas de consumo y monto
        estadisticas_consumo = queryset.aggregate(
            consumo_promedio=Avg('consumo'),
            consumo_total=Sum('consumo'),
            monto_promedio=Avg('monto'),
            monto_total=Sum('monto')
        )
        
        # Boletas vencidas
        vencidas = queryset.filter(
            fecha_vencimiento__lt=datetime.now().date(),
            estado_pago='pendiente'
        ).count()
        
        return Response({
            'total': total,
            'boletas_vencidas': vencidas,
            'por_estado_pago': list(por_estado_pago),
            'estadisticas_consumo': estadisticas_consumo
        })
    
    @action(detail=True, methods=['patch'])
    def actualizar_estado_pago(self, request, id_boleta=None):
        """
        Actualiza el estado de pago de una boleta
        
        PATCH /api/boletas/{id_boleta}/actualizar_estado_pago/
        Body: {"estado_pago": "pagada"}
        """
        boleta = self.get_object()
        nuevo_estado = request.data.get('estado_pago')
        
        if not nuevo_estado:
            return Response(
                {'error': 'Estado de pago requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el estado existe
        estados_validos = [choice[0] for choice in Boleta.ESTADOS_PAGO]
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Opciones: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        boleta.estado_pago = nuevo_estado
        boleta.save()
        
        serializer = self.get_serializer(boleta)
        return Response(serializer.data)


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
        
        GET /api/boletas/conversaciones/{session_id}/mensajes/
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
    
    POST /api/boletas/chat/init/
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
        
        # Iniciar conversación con el servicio de chatbot
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
    
    POST /api/boletas/chat/message/
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
        "boleta_id": null,
        "es_consulta_comparativa": false,
        ...
    }
    """
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    session_id = serializer.validated_data['session_id']
    user_message = serializer.validated_data['message']
    
    try:
        # Procesar mensaje con el servicio de chatbot
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
    
    GET /api/boletas/chat/status/{session_id}/
    
    Response:
    {
        "session_id": "uuid",
        "estado": "recolectando_datos",
        "datos_recolectados": {...},
        "boleta_id": "uuid" o null
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
    
    GET /api/boletas/rag/stats/
    
    Response:
    {
        "collection_name": "boletas_knowledge_base",
        "document_count": 42,
        "embedding_model": "..."
    }
    """
    try:
        # Implementar RAG
        from .RAG.retriever import get_rag_retriever
        
        rag_retriever = get_rag_retriever()
        collection_info = rag_retriever.get_collection_stats()
        
        return Response(collection_info)
        
    except Exception as e:
        logger.error(f"Error obteniendo stats RAG: {e}")
        return Response(
            {'error': 'Error al obtener estadísticas'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
