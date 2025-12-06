"""
Chatbot Service - Lógica conversacional para emergencias
Implementa el flujo del diagrama: entrevista → recolección de datos → cálculo de prioridad
"""
import google.generativeai as genai
from typing import Dict, Any, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
import logging
import json

from ..models import ChatConversation, ChatMessage, Emergencia
from ..RAG.retriever import get_rag_retriever

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Servicio principal del chatbot de emergencias
    """
    
    # Estados del flujo conversacional (según diagrama)
    STATE_INICIO = 'iniciada'
    STATE_RECOLECTANDO = 'recolectando_datos'
    STATE_CALCULANDO = 'calculando_prioridad'
    STATE_SOLICITANDO_CONTACTO = 'solicitando_contacto'
    STATE_FINALIZADA = 'finalizada'
    
    # Datos a recolectar (X1-X7 del diagrama)
    REQUIRED_DATA = {
        'sector': 'X1: Sector',
        'datos_medidor_fuga': 'X2: Datos del medidor/fuga',
        'fecha': 'X3: Fecha',
        'nombre_usuario': 'X4: Nombre del usuario',
        'fotografia': 'X5: Fotografía (opcional)',
        'direccion': 'X6: Dirección',
        'telefono': 'X7: Teléfono'
    }
    
    def __init__(self):
        """
        Inicializa el servicio del chatbot
        """
        # Configurar Gemini
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY no configurada")
        
        genai.configure(api_key=api_key)
        # Usar Gemini 2.5 Flash desde configuración
        gemini_model = getattr(settings, 'RAG_CONFIG', {}).get('gemini_model', 'gemini-2.5-flash')
        self.model = genai.GenerativeModel(gemini_model)
        
        # Inicializar RAG
        self.rag_retriever = get_rag_retriever()
        
        logger.info("ChatbotService inicializado")
    
    def start_conversation(self, session_id: str) -> Tuple[ChatConversation, str]:
        """
        Inicia una nueva conversación
        
        Args:
            session_id: ID único de la sesión
            
        Returns:
            Tuple con (ChatConversation, mensaje_inicial)
        """
        # Crear conversación
        conversation = ChatConversation.objects.create(
            session_id=session_id,
            estado=self.STATE_INICIO,
            datos_recolectados={}
        )
        
        # Mensaje inicial (según diagrama: "Chatbot entrevista al usuario")
        mensaje_inicial = self._get_initial_message()
        
        # Guardar mensaje del sistema
        ChatMessage.objects.create(
            conversation=conversation,
            rol='sistema',
            contenido=mensaje_inicial
        )
        
        # Actualizar estado
        conversation.estado = self.STATE_RECOLECTANDO
        conversation.save()
        
        logger.info(f"Conversación iniciada: {session_id}")
        return conversation, mensaje_inicial
    
    def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario
        
        Args:
            session_id: ID de la sesión
            user_message: Mensaje del usuario
            
        Returns:
            Dict con respuesta y estado
        """
        try:
            # Obtener o crear conversación
            conversation = ChatConversation.objects.get(session_id=session_id)
            
            # Guardar mensaje del usuario
            ChatMessage.objects.create(
                conversation=conversation,
                rol='usuario',
                contenido=user_message
            )
            
            # Procesar según estado actual
            if conversation.estado == self.STATE_RECOLECTANDO:
                response = self._handle_data_collection(conversation, user_message)
            
            elif conversation.estado == self.STATE_SOLICITANDO_CONTACTO:
                response = self._handle_contact_request(conversation, user_message)
            
            else:
                response = {
                    'message': 'Conversación finalizada o en estado inválido',
                    'estado': conversation.estado,
                    'completed': True
                }
            
            # Guardar respuesta del asistente
            ChatMessage.objects.create(
                conversation=conversation,
                rol='asistente',
                contenido=response['message']
            )
            
            return response
            
        except ChatConversation.DoesNotExist:
            logger.error(f"Conversación no encontrada: {session_id}")
            return {
                'error': 'Sesión no encontrada',
                'message': 'Por favor inicia una nueva conversación',
                'estado': 'error'
            }
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return {
                'error': str(e),
                'message': 'Ocurrió un error procesando tu mensaje',
                'estado': 'error'
            }
    
    def _handle_data_collection(
        self,
        conversation: ChatConversation,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Maneja la recolección de datos X1-X7
        
        Args:
            conversation: Conversación activa
            user_message: Mensaje del usuario
            
        Returns:
            Dict con respuesta
        """
        # Obtener datos ya recolectados
        datos = conversation.datos_recolectados
        
        # Usar Gemini + RAG para extraer información
        extracted_data = self._extract_data_with_llm(
            user_message,
            datos,
            conversation
        )
        
        # Actualizar datos recolectados
        datos.update(extracted_data)
        conversation.datos_recolectados = datos
        conversation.save()
        
        # Verificar si faltan datos
        missing_data = self._get_missing_data(datos)
        
        if missing_data:
            # Solicitar datos faltantes
            next_question = self._ask_for_missing_data(missing_data, datos)
            return {
                'message': next_question,
                'estado': conversation.estado,
                'datos_recolectados': list(datos.keys()),
                'datos_faltantes': missing_data,
                'completed': False
            }
        else:
            # Todos los datos recolectados -> calcular prioridad
            return self._calculate_priority(conversation)
    
    def _extract_data_with_llm(
        self,
        user_message: str,
        current_data: Dict,
        conversation: ChatConversation
    ) -> Dict[str, Any]:
        """
        Extrae información del mensaje usando Gemini + RAG
        
        Args:
            user_message: Mensaje del usuario
            current_data: Datos ya recolectados
            conversation: Conversación activa
            
        Returns:
            Dict con datos extraídos
        """
        # Obtener contexto relevante del RAG
        context = self.rag_retriever.get_relevant_context_text(
            query=user_message,
            max_length=2000
        )
        
        # Obtener historial reciente
        history = self._get_conversation_history(conversation, last_n=5)
        
        # Construir prompt
        prompt = self._build_extraction_prompt(
            user_message,
            current_data,
            context,
            history
        )
        
        try:
            # Llamar a Gemini
            response = self.model.generate_content(prompt)
            
            # Parsear respuesta JSON
            extracted = json.loads(response.text)
            
            logger.info(f"Datos extraídos: {list(extracted.keys())}")
            return extracted
            
        except json.JSONDecodeError:
            logger.warning("Respuesta de LLM no es JSON válido")
            return {}
        except Exception as e:
            logger.error(f"Error en extracción con LLM: {e}")
            return {}
    
    def _build_extraction_prompt(
        self,
        user_message: str,
        current_data: Dict,
        rag_context: str,
        history: List[Dict]
    ) -> str:
        """
        Construye el prompt para extracción de datos
        """
        history_text = "\n".join([
            f"{msg['rol']}: {msg['contenido']}"
            for msg in history
        ])
        
        current_data_text = json.dumps(current_data, indent=2, ensure_ascii=False)
        
        prompt = f"""Eres un asistente especializado en emergencias de agua potable de la Cooperativa de Agua Potable.

{rag_context}

HISTORIAL DE CONVERSACIÓN:
{history_text}

DATOS YA RECOLECTADOS:
{current_data_text}

MENSAJE ACTUAL DEL USUARIO:
{user_message}

Tu tarea es extraer la siguiente información del mensaje del usuario y el contexto:

1. sector: Uno de [anibana, el_molino, la_compania, el_maiten_1, la_morera, el_maiten_2, santa_margarita]
2. datos_medidor_fuga: Información sobre si el medidor corre, cantidad de agua, tipo de fuga
3. fecha: Fecha actual o mencionada (formato YYYY-MM-DD)
4. nombre_usuario: Nombre del usuario
5. fotografia: Si mencionó que tiene foto (true/false)
6. direccion: Dirección completa
7. telefono: Número de teléfono (formato limpio)
8. tipo_emergencia: Tipo de problema [rotura_matriz, baja_presion, fuga_agua, caneria_rota, agua_contaminada, sin_agua, otro]
9. descripcion: Descripción detallada del problema

INSTRUCCIONES:
- Solo extrae datos que estén EXPLÍCITAMENTE mencionados
- No inventes información
- Mantén datos ya recolectados si no hay nueva información
- Responde SOLO con un objeto JSON válido
- Si un dato no está presente, no lo incluyas en el JSON

Ejemplo de respuesta:
{{
  "sector": "el_molino",
  "telefono": "981494350",
  "descripcion": "Se rompió una cañería"
}}

Responde SOLO con JSON:"""
        
        return prompt
    
    def _get_missing_data(self, datos: Dict) -> List[str]:
        """
        Identifica qué datos faltan por recolectar
        """
        missing = []
        
        # Datos obligatorios (fotografia es opcional)
        required = ['sector', 'nombre_usuario', 'direccion', 'telefono', 'descripcion']
        
        for key in required:
            if key not in datos or not datos[key]:
                missing.append(key)
        
        return missing
    
    def _ask_for_missing_data(
        self,
        missing_data: List[str],
        current_data: Dict
    ) -> str:
        """
        Genera pregunta para solicitar datos faltantes
        """
        # Mapeo de campos a preguntas amigables
        questions = {
            'sector': '¿En qué sector te encuentras? (Anibana, El Molino, La Compañía, El Maitén 1, La Morera, El Maitén 2, Santa Margarita)',
            'datos_medidor_fuga': '¿Podrías indicarme si el medidor está corriendo y aproximadamente cuánta agua se está fugando?',
            'nombre_usuario': '¿Cuál es tu nombre?',
            'fotografia': '¿Tienes una fotografía del problema que puedas compartir? (Opcional)',
            'direccion': '¿Cuál es tu dirección exacta?',
            'telefono': '¿Cuál es tu número de teléfono de contacto?',
            'descripcion': '¿Podrías describir detalladamente el problema que estás enfrentando?',
            'tipo_emergencia': '¿Qué tipo de emergencia es? (rotura de matriz, baja presión, fuga, cañería rota, agua contaminada, sin agua, otro)'
        }
        
        # Preguntar por el primer dato faltante
        next_field = missing_data[0]
        question = questions.get(next_field, f'Por favor proporciona: {next_field}')
        
        # Agregar contexto de progreso
        total_required = 7
        collected = total_required - len(missing_data)
        
        progress = f"\n\n📊 Progreso: {collected}/{total_required} datos recolectados"
        
        return question + progress
    
    def _calculate_priority(self, conversation: ChatConversation) -> Dict[str, Any]:
        """
        Calcula prioridad y crea la emergencia (según diagrama)
        """
        conversation.estado = self.STATE_CALCULANDO
        conversation.save()
        
        datos = conversation.datos_recolectados
        
        # Crear emergencia
        emergencia = Emergencia.objects.create(
            nombre_usuario=datos.get('nombre_usuario', ''),
            telefono=datos.get('telefono', ''),
            sector=datos.get('sector', 'el_molino'),
            direccion=datos.get('direccion', ''),
            descripcion=datos.get('descripcion', ''),
            tipo_emergencia=datos.get('tipo_emergencia', 'otro'),
            medidor_corriendo=datos.get('medidor_corriendo', None),
            cantidad_agua=datos.get('cantidad_agua', ''),
        )
        
        # Calcular prioridad automáticamente
        emergencia.calcular_prioridad()
        emergencia.save()
        
        # Asociar emergencia a conversación
        conversation.emergencia = emergencia
        conversation.estado = self.STATE_SOLICITANDO_CONTACTO
        conversation.save()
        
        # Mensaje sobre la prioridad
        prioridad_msg = self._get_priority_message(emergencia)
        
        # Preguntar por contacto colaborativo (según diagrama)
        contacto_msg = "\n\n¿Deseas que te proporcionemos datos de contacto de colaboradores de la cooperativa?"
        
        return {
            'message': prioridad_msg + contacto_msg,
            'estado': conversation.estado,
            'emergencia_id': str(emergencia.id_emergencia),
            'nivel_prioridad': emergencia.nivel_prioridad,
            'completed': False
        }
    
    def _handle_contact_request(
        self,
        conversation: ChatConversation,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Maneja solicitud de contacto colaborativo (decisión final del diagrama)
        """
        # Detectar si dice sí o no
        respuesta_lower = user_message.lower()
        solicita_contacto = any(word in respuesta_lower for word in ['sí', 'si', 'yes', 'ok', 'claro', 'por favor'])
        
        # Actualizar emergencia
        if conversation.emergencia:
            conversation.emergencia.solicita_contacto_colaborativo = solicita_contacto
            conversation.emergencia.save()
        
        # Finalizar conversación
        conversation.estado = self.STATE_FINALIZADA
        conversation.fecha_fin = timezone.now()
        conversation.save()
        
        if solicita_contacto:
            # Proporcionar contactos (del RAG o directos)
            contactos_msg = self._get_contacts_message()
            final_msg = f"{contactos_msg}\n\n✅ Tu emergencia ha sido registrada exitosamente. El personal operativo será notificado según la prioridad asignada.\n\n¡Gracias por reportar!"
        else:
            final_msg = "✅ Tu emergencia ha sido registrada exitosamente. El personal operativo será notificado según la prioridad asignada.\n\n¡Gracias por reportar!"
        
        return {
            'message': final_msg,
            'estado': conversation.estado,
            'emergencia_id': str(conversation.emergencia.id_emergencia) if conversation.emergencia else None,
            'completed': True
        }
    
    def _get_initial_message(self) -> str:
        """
        Mensaje inicial del chatbot
        """
        return """¡Hola! Soy el asistente virtual de la Cooperativa de Agua Potable. 

Estoy aquí para ayudarte a reportar una emergencia relacionada con el servicio de agua potable.

Por favor, cuéntame qué situación estás enfrentando y te guiaré en el proceso de reporte."""
    
    def _get_priority_message(self, emergencia: Emergencia) -> str:
        """
        Mensaje explicando la prioridad asignada
        """
        prioridad_map = {
            'baja': '🟢 BAJA - Se atenderá en horario normal',
            'media': '🟡 MEDIA - Se atenderá con prioridad',
            'alta': '🟠 ALTA - Se atenderá urgentemente',
            'critica': '🔴 CRÍTICA - Se atenderá de inmediato'
        }
        
        nivel_texto = prioridad_map.get(emergencia.nivel_prioridad, 'MEDIA')
        
        return f"""✅ Hemos registrado tu emergencia exitosamente.

📋 **Resumen:**
- Tipo: {emergencia.get_tipo_emergencia_display()}
- Sector: {emergencia.get_sector_display()}
- Prioridad: {nivel_texto}

{self._get_priority_explanation(emergencia.nivel_prioridad)}"""
    
    def _get_priority_explanation(self, nivel: str) -> str:
        """
        Explicación del nivel de prioridad
        """
        explanations = {
            'baja': 'Tu reporte será atendido durante el horario normal de operación (hasta las 17:00).',
            'media': 'Tu reporte será atendido con prioridad por nuestro equipo operativo.',
            'alta': 'Tu reporte será atendido urgentemente. El equipo se contactará contigo pronto.',
            'critica': 'Tu reporte es crítico y será atendido de inmediato, incluso fuera del horario normal.'
        }
        return explanations.get(nivel, '')
    
    def _get_contacts_message(self) -> str:
        """
        Mensaje con contactos de la cooperativa
        """
        return """📞 **Contactos de la Cooperativa:**

- **Recaudación:** +56 9 8149 4350
- **Gerente:** +56 9 7846 7011  
- **Operador:** +56 9 5403 8948
- **Correo:** laciacoop@gmail.com

Horario de atención: Lunes a Viernes, 08:00 - 17:00
Teléfono de emergencias: +56 9 5403 8948 (24/7)"""
    
    def _get_conversation_history(
        self,
        conversation: ChatConversation,
        last_n: int = 5
    ) -> List[Dict[str, str]]:
        """
        Obtiene el historial reciente de la conversación
        """
        messages = conversation.mensajes.order_by('-timestamp')[:last_n]
        history = []
        
        for msg in reversed(messages):
            history.append({
                'rol': msg.rol,
                'contenido': msg.contenido
            })
        
        return history


# Singleton
_chatbot_service_instance = None


def get_chatbot_service() -> ChatbotService:
    """
    Obtiene la instancia singleton del ChatbotService
    
    Returns:
        ChatbotService: Instancia del servicio
    """
    global _chatbot_service_instance
    if _chatbot_service_instance is None:
        _chatbot_service_instance = ChatbotService()
    return _chatbot_service_instance
