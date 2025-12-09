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
import unicodedata

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
    
    @action(detail=False, methods=['post'], url_path='consultar')
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
        # Agregar logging detallado para diagnosticar 400s desde el frontend
        try:
            logger.debug(f"Consultar boletas - request.content_type={request.content_type}")
            logger.debug(f"Consultar boletas - request.META keys: {list(request.META.keys())[:20]}")
            # Intentar leer el body crudo primero (puede fallar si ya fue consumido)
            raw = ''
            try:
                raw = request.body.decode('utf-8') if getattr(request, 'body', None) else ''
            except Exception as ex:
                # Evitar RawPostDataException que ocurre si request.data ya fue leído
                raw = f'<raw body not available: {ex.__class__.__name__}>'
            logger.debug(f"Consultar boletas - raw body: {raw}")

            # request.data puede procesar el body; loguearlo (siempre que no sea muy grande)
            try:
                logger.debug(f"Consultar boletas - request.data: {request.data}")
            except Exception:
                logger.debug("Consultar boletas - request.data: <no disponible>")

            serializer = BoletaConsultaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
        except Exception as e:
            # Registrar error y devolver detalle en la respuesta para facilitar debugging
            logger.error("Error validando BoletaConsultaSerializer", exc_info=True)
            # Si es un ValidationError de DRF, extraer detalles
            from rest_framework.exceptions import ValidationError
            if isinstance(e, ValidationError):
                logger.error(f"Validation errors: {e.detail}")
                return Response({'error': 'Validation error', 'detail': e.detail}, status=status.HTTP_400_BAD_REQUEST)
            # En caso contrario, devolver un error genérico con el mensaje
            return Response({'error': 'Error procesando la solicitud', 'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        queryset = Boleta.objects.all()
        
        # Aplicar filtros
        # Only filter by rut when a non-empty value is provided
        if data.get('rut'):
            queryset = queryset.filter(rut=data['rut'])
        # Soportar búsqueda por nombre completo (campo 'nombre' o 'nombreCompleto' desde frontend)
        # Normalize search name and try accent-insensitive fallback
        search_name = None
        if data.get('nombre'):
            search_name = data.get('nombre')
        elif data.get('nombreCompleto'):
            search_name = data.get('nombreCompleto')

        if search_name:
            # Accent-insensitive match by normalizing both DB values and search term in Python
            def strip_accents(s):
                return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

            target = strip_accents(search_name).lower()
            # Break target into tokens to allow partial & reordered name matches
            tokens = [t for t in target.split() if t]

            # Collect matching ids by iterating names (SQLite doesn't have unaccent)
            candidates = queryset.values_list('id_boleta', 'nombre')
            matching_ids = []
            for _id, nombre in candidates:
                if not nombre:
                    continue
                nombre_norm = strip_accents(nombre).lower()
                # Require that all tokens appear in the normalized nombre (order-insensitive)
                if all(tok in nombre_norm for tok in tokens):
                    matching_ids.append(_id)

            # Log debug info to help diagnose no-results cases
            try:
                logger.debug(f"Buscar por nombre: search_name={search_name!r}, tokens={tokens}, matches={len(matching_ids)}")
            except Exception:
                logger.debug("Buscar por nombre: debug info unavailable")

            # Filter queryset to only matching ids (if none, result will be empty)
            if matching_ids:
                queryset = queryset.filter(id_boleta__in=matching_ids)
            else:
                # No matches found with strict token inclusion; try a looser substring fallback
                fallback_ids = []
                for _id, nombre in candidates:
                    if not nombre:
                        continue
                    nombre_norm = strip_accents(nombre).lower()
                    if target in nombre_norm:
                        fallback_ids.append(_id)
                logger.debug(f"Buscar por nombre: fallback matches={len(fallback_ids)}")
                if fallback_ids:
                    queryset = queryset.filter(id_boleta__in=fallback_ids)
        if data.get('periodo'):
            queryset = queryset.filter(periodo_facturacion=data['periodo'])
        # permitir filtrar por estado de pago
        if data.get('estado_pago'):
            queryset = queryset.filter(estado_pago=data['estado_pago'])
        # si solicitan solo la boleta vigente para pagar (la más reciente pendiente)
        if data.get('solo_vigente'):
            queryset = queryset.filter(estado_pago='pendiente')
            boleta_vigente = queryset.order_by('-fecha_emision').first()
            detalle = bool(request.data.get('detailed') or request.data.get('detalle'))
            if not boleta_vigente:
                return Response([], status=status.HTTP_200_OK)
            serializer_cls = BoletaSerializer if detalle else BoletaSimpleSerializer
            serializer = serializer_cls(boleta_vigente)
            return Response(serializer.data)
        if 'fecha_inicio' in data:
            queryset = queryset.filter(fecha_emision__gte=data['fecha_inicio'])
        if 'fecha_fin' in data:
            queryset = queryset.filter(fecha_emision__lte=data['fecha_fin'])
        
        queryset = queryset.order_by('-fecha_emision')
        try:
            logger.debug(f"Consultar boletas - queryset SQL: {queryset.query}")
            logger.debug(f"Consultar boletas - queryset count (pre-paginate): {queryset.count()}")
        except Exception:
            logger.debug("Consultar boletas - queryset debug unavailable")
        
        # Determinar el nivel de detalle: por defecto mostramos datos resumidos
        detalle = False
        if request.data and isinstance(request.data, dict):
            detalle = bool(request.data.get('detailed') or request.data.get('detalle'))
        # Paginar resultados
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer_cls = BoletaSerializer if detalle else BoletaSimpleSerializer
            serializer = serializer_cls(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer_cls = BoletaSerializer if detalle else BoletaSimpleSerializer
        serializer = serializer_cls(queryset, many=True)
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
        
        # Determinar nivel de detalle (por defecto resumido)
        detalle = request.query_params.get('detailed', request.query_params.get('detalle', 'false')).lower() == 'true'
        # Paginar resultados
        page = self.paginate_queryset(boletas)
        serializer_cls = BoletaSerializer if detalle else BoletaSimpleSerializer
        if page is not None:
            serializer = serializer_cls(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializer_cls(boletas, many=True)
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

        # If explicit boletas_ids provided, retrieve those
        if boletas_ids:
            boletas = Boleta.objects.filter(id_boleta__in=boletas_ids)
        # If rut + periodos provided, retrieve those
        elif rut and periodos:
            boletas = Boleta.objects.filter(rut=rut, periodo_facturacion__in=periodos)
        # If only rut provided, return candidate boletas for selection
        elif rut:
            candidates = Boleta.objects.filter(rut=rut).order_by('-fecha_emision')[:12]
            serializer = BoletaSimpleSerializer(candidates, many=True)
            return Response({'candidates': serializer.data})
        else:
            return Response(
                {'error': 'Debe proporcionar boletas_ids o rut'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not boletas.exists():
            return Response(
                {'error': 'No se encontraron boletas para comparar'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calcular estadísticas
        consumo_total = boletas.aggregate(Sum('consumo'))['consumo__sum'] or 0
        monto_total = boletas.aggregate(Sum('monto'))['monto__sum'] or 0
        consumo_promedio = boletas.aggregate(Avg('consumo'))['consumo__avg'] or 0
        monto_promedio = boletas.aggregate(Avg('monto'))['monto__avg'] or 0

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
    
    user_message = serializer.validated_data['message']

    # Support passing boletas_ids from frontend to provide immediate context
    boletas_ids = request.data.get('boletas_ids', [])

    try:
        # Ensure we have a chatbot service instance
        chatbot_service = get_chatbot_service()

        # session_id may be optional from frontend; create one if missing
        session_id = serializer.validated_data.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            # start a conversation so it's available for processing
            try:
                conversation, initial_message = chatbot_service.start_conversation(session_id)
            except Exception as e:
                logger.warning(f"No se pudo iniciar conversación automáticamente: {e}")
        

        # If boletas_ids provided, attach boletas to the conversation for context
        if boletas_ids:
            try:
                conversation = ChatConversation.objects.get(session_id=session_id)
                from .models import Boleta as _Boleta
                boletas_qs = _Boleta.objects.filter(id_boleta__in=boletas_ids).order_by('-fecha_emision')
                if boletas_qs.exists():
                    # set boleta_principal to the most recent selected
                    first = boletas_qs.first()
                    datos = conversation.datos_recolectados or {}
                    datos['rut'] = first.rut
                    conversation.datos_recolectados = datos
                    conversation.boleta_principal = first
                    # set many-to-many of compared boletas
                    conversation.boletas_comparadas.set(boletas_qs)
                    conversation.es_consulta_comparativa = boletas_qs.count() > 1
                    # set state accordingly
                    conversation.estado = 'comparando' if boletas_qs.count() > 1 else 'consultando'
                    conversation.save()
            except Exception as e:
                logger.warning(f"No se pudo adjuntar boletas al contexto de la conversación: {e}")

        # Procesar mensaje con el servicio de chatbot
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


@api_view(['POST'])
def public_chat_message(request):
    """
    Endpoint público para preguntas generales (anónimas).

    POST /api/public/chat/message/
    Body: { "message": "texto de la consulta" }

    Este endpoint utiliza únicamente el RAG retriever y el modelo para
    generar una respuesta concisa sin crear ni persistir conversaciones
    en la base de datos. No se deben solicitar ni registrar datos personales.
    """
    try:
        data = request.data or {}
        user_message = data.get('message', '')
        if not user_message:
            return Response({'error': 'message field requerido'}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener contexto RAG (si está disponible)
        try:
            from .RAG.retriever import get_rag_retriever
            rag_retriever = get_rag_retriever()
            rag_context = rag_retriever.get_relevant_context_text(query=user_message, max_length=1500)
        except Exception as e:
            logger.warning(f"No se pudo obtener contexto RAG: {e}")
            rag_context = ""

        # Construir prompt para respuesta anónima y breve
        prompt = f"""Eres un asistente público y anónimo para la Cooperativa de Agua.
    Usa únicamente la información pública disponible (si existe) y responde de forma clara y útil.
    No pidas ni solicites datos personales (RUT, número de cliente, teléfono, etc.).

    Contexto recuperado (fragmentos con fuente):
    {rag_context}

    Pregunta del usuario:
    {user_message}

    Instrucciones de formato:
    - Responde en 4-6 oraciones claras y útiles.
    - Incluye al final una línea corta con referencias a las fuentes usadas en formato: "Fuentes: [1] URL, [2] URL" (usa los índices provistos en el contexto si están disponibles).
    - Si no hay información en la base de conocimientos, indica que no se encontró y sugiere cómo el usuario puede contactar a la cooperativa.
    - No solicites datos personales en ningún caso."""

        # Generar respuesta usando el modelo (sin crear conversaciones)
        chatbot_service = get_chatbot_service()
        try:
            # Increase allowed tokens to reduce chance of truncated replies
            response = chatbot_service.model.generate_content(prompt, generation_config={'temperature': 0.1, 'max_output_tokens': 400})
            bot_text = response.text.strip()
            # If the response looks too short or abruptly cut, do one retry asking to expand
            short_threshold = 40
            ends_proper = bot_text.endswith('.') or bot_text.endswith('!') or bot_text.endswith('?')
            if (not bot_text) or (len(bot_text) < short_threshold) or (not ends_proper):
                logger.info('Public chat response appears short or incomplete; attempting one retry to expand it')
                followup_prompt = f"""La respuesta anterior fue:
{bot_text}

Por favor, completa y expande la respuesta anterior en 3-4 frases útiles, sin pedir datos personales, manteniendo el mismo tono amistoso y claro."""
                try:
                    follow_resp = chatbot_service.model.generate_content(followup_prompt, generation_config={'temperature': 0.15, 'max_output_tokens': 300})
                    follow_text = follow_resp.text.strip()
                    if follow_text:
                        bot_text = follow_text
                except Exception as re:
                    logger.warning(f"Retry to expand public response failed: {re}")
        except Exception as e:
            msg = str(e).lower()
            if 'quota' in msg or '429' in msg or 'rate limit' in msg or 'quota exceeded' in msg:
                logger.warning(f"Public chat generation failed due to quota/rate-limit: {e}")
                return Response({'message': 'Disculpa, el servicio de generación está temporalmente limitado por cuota. Por favor intenta de nuevo en unos segundos.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            logger.error(f"Error generando respuesta pública: {e}")
            return Response({'error': 'Error generando respuesta', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': bot_text})

    except Exception as e:
        logger.error(f"Error en public_chat_message: {e}")
        return Response({'error': 'Error procesando petición', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
