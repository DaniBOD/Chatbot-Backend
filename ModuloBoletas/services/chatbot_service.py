"""
Chatbot Service - Lógica conversacional para consultas de boletas de agua
Implementa el flujo del diagrama: 
1. Iniciar conversación
2. Preguntar motivo de consulta
3. Verificar si tiene boleta en sistema
4. Si NO tiene boleta → solicitar imagen
5. Si SÍ tiene boleta → rescatar datos y responder
6. Verificar si consulta es comparativa → responder acorde
"""
import google.generativeai as genai
from typing import Dict, Any, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import json
import re

from ..models import ChatConversation, ChatMessage, Boleta
from ..RAG.retriever import get_rag_retriever

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Servicio principal del chatbot de boletas de agua
    """
    
    # Estados del flujo conversacional (según diagrama)
    STATE_INICIO = 'iniciada'
    STATE_RECOLECTANDO = 'recolectando_datos'
    STATE_CONSULTANDO = 'consultando'
    STATE_COMPARANDO = 'comparando'
    STATE_FINALIZADA = 'finalizada'
    
    # Datos a recolectar
    REQUIRED_DATA = {
        'motivo_consulta': 'Motivo de consulta',
        'rut': 'RUT del cliente',
        'tiene_boleta': 'Si tiene boleta en el sistema',
    }
    
    # Motivos de consulta válidos
    MOTIVOS_CONSULTA = [
        'ver_boleta',
        'consultar_monto',
        'consultar_consumo',
        'comparar_periodos',
        'estado_pago',
        'informacion_general',
        'otro'
    ]
    
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
        try:
            self.rag_retriever = get_rag_retriever()
            logger.info("RAG retriever inicializado correctamente")
        except Exception as e:
            logger.warning(f"No se pudo inicializar RAG: {e}")
            self.rag_retriever = None
        
        logger.info("ChatbotService (Boletas) inicializado")
    
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
        
        # Mensaje inicial
        mensaje_inicial = self._get_initial_message()
        
        # Guardar mensaje del sistema
        ChatMessage.objects.create(
            conversation=conversation,
            rol='asistente',
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
        Procesa un mensaje del usuario según el flujo del diagrama
        
        Args:
            session_id: ID de la sesión
            user_message: Mensaje del usuario
            
        Returns:
            Dict con respuesta y estado
        """
        try:
            # Obtener conversación
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
            
            elif conversation.estado == self.STATE_CONSULTANDO:
                response = self._handle_consultation(conversation, user_message)
            
            elif conversation.estado == self.STATE_COMPARANDO:
                response = self._handle_comparison(conversation, user_message)
            
            else:
                response = {
                    'message': 'Conversación finalizada. Puedes iniciar una nueva conversación.',
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
                'message': 'Ocurrió un error procesando tu mensaje. Por favor intenta nuevamente.',
                'estado': 'error'
            }
    
    def _handle_data_collection(
        self,
        conversation: ChatConversation,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Maneja la recolección de datos inicial (motivo y RUT)
        Flujo: Preguntar motivo → Verificar si tiene boleta
        
        Args:
            conversation: Conversación activa
            user_message: Mensaje del usuario
            
        Returns:
            Dict con respuesta
        """
        datos = conversation.datos_recolectados
        
        # Extraer información usando LLM
        extracted_data = self._extract_data_with_llm(
            user_message,
            datos,
            conversation
        )
        
        # Actualizar datos recolectados
        datos.update(extracted_data)
        conversation.datos_recolectados = datos
        conversation.save()
        
        # Verificar qué datos faltan
        if 'motivo_consulta' not in datos:
            return {
                'message': '¿En qué puedo ayudarte hoy? Puedes:\n\n' +
                           '• Ver tu boleta actual\n' +
                           '• Consultar el monto a pagar\n' +
                           '• Revisar tu consumo\n' +
                           '• Comparar consumos entre períodos\n' +
                           '• Verificar el estado de pago\n' +
                           '• Otra consulta',
                'estado': conversation.estado,
                'completed': False
            }
        
        if 'rut' not in datos:
            # Mensaje más amigable dependiendo del motivo
            motivo = datos.get('motivo_consulta', '')
            if 'compar' in motivo:
                mensaje_rut = '¡Perfecto! Para comparar tus boletas, necesito tu RUT. Por favor indícamelo (formato: 12345678-9)'
            elif 'monto' in motivo or 'pagar' in motivo:
                mensaje_rut = 'Entendido, para consultar el monto a pagar necesito tu RUT. Por favor indícamelo (formato: 12345678-9)'
            elif 'consumo' in motivo:
                mensaje_rut = 'Claro, para revisar tu consumo necesito tu RUT. Por favor indícamelo (formato: 12345678-9)'
            elif 'estado' in motivo:
                mensaje_rut = 'De acuerdo, para verificar el estado necesito tu RUT. Por favor indícamelo (formato: 12345678-9)'
            else:
                mensaje_rut = '¡Perfecto! Para ayudarte, necesito tu RUT. Por favor indícamelo (formato: 12345678-9)'
            
            return {
                'message': mensaje_rut,
                'estado': conversation.estado,
                'completed': False
            }
        
        # Ya tenemos motivo y RUT, verificar si tiene boleta
        return self._verificar_boleta_en_sistema(conversation)
    
    def _verificar_boleta_en_sistema(
        self,
        conversation: ChatConversation
    ) -> Dict[str, Any]:
        """
        Verifica si el RUT tiene boletas en el sistema (Paso 3 del diagrama)
        """
        datos = conversation.datos_recolectados
        rut = datos.get('rut')
        
        # Buscar boletas del RUT
        boletas = Boleta.objects.filter(rut=rut).order_by('-fecha_emision')
        
        if not boletas.exists():
            # NO tiene boleta → solicitar imagen (Paso 4 del diagrama)
            datos['tiene_boleta'] = False
            conversation.datos_recolectados = datos
            conversation.save()
            
            return {
                'message': 'No encontré boletas registradas con tu RUT en nuestro sistema.\n\n' +
                           '📸 Por favor, envíame una foto de tu boleta para poder ayudarte. ' +
                           'Una vez que la reciba, podré registrarla y responder tus consultas.',
                'estado': conversation.estado,
                'completed': False,
                'tiene_boleta': False
            }
        else:
            # SÍ tiene boleta → rescatar datos y responder (Paso 5 del diagrama)
            datos['tiene_boleta'] = True
            conversation.datos_recolectados = datos
            
            # Obtener boleta más reciente
            boleta_reciente = boletas.first()
            conversation.boleta_principal = boleta_reciente
            
            # Verificar si es consulta comparativa
            motivo = datos.get('motivo_consulta', '')
            es_comparativa = 'compar' in motivo.lower()
            conversation.es_consulta_comparativa = es_comparativa
            
            if es_comparativa:
                conversation.estado = self.STATE_COMPARANDO
            else:
                conversation.estado = self.STATE_CONSULTANDO
            
            conversation.save()
            
            # Responder según el motivo
            return self._responder_segun_motivo(conversation, boleta_reciente, boletas)
    
    def _responder_segun_motivo(
        self,
        conversation: ChatConversation,
        boleta_principal: Boleta,
        todas_boletas: Any
    ) -> Dict[str, Any]:
        """
        Genera respuesta según el motivo de consulta
        """
        datos = conversation.datos_recolectados
        motivo = datos.get('motivo_consulta', '').lower()
        
        # Información de la boleta principal
        info_boleta = self._formatear_info_boleta(boleta_principal)
        
        if 'compar' in motivo:
            # Consulta comparativa
            if todas_boletas.count() < 2:
                mensaje = (f"Solo encontré una boleta en el sistema:\n\n{info_boleta}\n\n"
                         "Para poder hacer comparaciones, necesitamos al menos dos boletas registradas.")
            else:
                mensaje = self._generar_comparacion(todas_boletas[:3])  # Últimas 3 boletas
            
            return {
                'message': mensaje,
                'estado': conversation.estado,
                'boleta_id': str(boleta_principal.id_boleta),
                'es_consulta_comparativa': True,
                'completed': False
            }
        
        elif 'monto' in motivo or 'pagar' in motivo or 'pago' in motivo:
            mensaje = f"💵 **Información de Pago**\n\n{info_boleta}\n\n"
            if boleta_principal.esta_vencida():
                mensaje += "⚠️ **BOLETA VENCIDA** - Te recomendamos realizar el pago lo antes posible para evitar cortes de servicio."
            else:
                dias_vencimiento = (boleta_principal.fecha_vencimiento - timezone.now().date()).days
                mensaje += f"✅ Tienes **{dias_vencimiento} días** hasta el vencimiento."
        
        elif 'consumo' in motivo:
            mensaje = f"📊 **Información de Consumo**\n\n{info_boleta}\n\n"
            promedio = boleta_principal.get_consumo_promedio_diario()
            if promedio:
                consumo_diario = f"{promedio} m³/día"
                mensaje += f"📈 Tu consumo promedio diario es de **{consumo_diario}**"
        
        elif 'estado' in motivo:
            mensaje = f"📋 **Estado de tu Boleta**\n\n{info_boleta}"
        
        else:
            # Información general
            mensaje = f"📄 **Tu Boleta Actual**\n\n{info_boleta}\n\n¿Tienes alguna pregunta adicional sobre tu boleta?"
        
        return {
            'message': mensaje,
            'estado': conversation.estado,
            'boleta_id': str(boleta_principal.id_boleta),
            'completed': False
        }
    
    def _handle_consultation(
        self,
        conversation: ChatConversation,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Maneja consultas adicionales en estado de consulta
        """
        # Usar Gemini para responder con contexto de la boleta
        boleta = conversation.boleta_principal
        
        if not boleta:
            return {
                'message': 'No pude encontrar tu boleta. ¿Podrías proporcionarme tu RUT nuevamente?',
                'estado': self.STATE_RECOLECTANDO,
                'completed': False
            }
        
        # Generar respuesta contextual con LLM
        response_text = self._generate_contextual_response(
            user_message,
            boleta,
            conversation
        )
        
        # Preguntar si necesita algo más
        response_text += "\n\n¿Hay algo más en lo que pueda ayudarte con tu boleta?"
        
        return {
            'message': response_text,
            'estado': conversation.estado,
            'boleta_id': str(boleta.id_boleta),
            'completed': False
        }
    
    def _handle_comparison(
        self,
        conversation: ChatConversation,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Maneja consultas comparativas
        """
        rut = conversation.datos_recolectados.get('rut')
        boletas = Boleta.objects.filter(rut=rut).order_by('-fecha_emision')[:6]
        
        if boletas.count() < 2:
            mensaje = "Solo tienes una boleta registrada. Para comparaciones necesitas al menos dos boletas."
        else:
            # Generar análisis comparativo con LLM
            mensaje = self._generate_comparative_analysis(user_message, boletas, conversation)
        
        return {
            'message': mensaje,
            'estado': conversation.estado,
            'es_consulta_comparativa': True,
            'completed': False
        }
    
    def _extract_data_with_llm(
        self,
        user_message: str,
        current_data: Dict,
        conversation: ChatConversation
    ) -> Dict[str, Any]:
        """
        Extrae información del mensaje usando Gemini (primario) con fallback a regex
        
        Args:
            user_message: Mensaje del usuario
            current_data: Datos ya recolectados
            conversation: Conversación actual
            
        Returns:
            Dict con los datos extraídos
        """
        extracted_data = {}
        
        # MÉTODO PRIMARIO: Extracción con LLM (Gemini)
        logger.info("🤖 Intentando extracción con Gemini API...")
        
        try:
            # Obtener historial reciente
            history = self._get_conversation_history(conversation, last_n=3)
            
            # Obtener contexto del RAG si está disponible
            rag_context = ""
            if self.rag_retriever:
                try:
                    rag_context = self.rag_retriever.get_relevant_context_text(
                        query=user_message,
                        max_length=1000
                    )
                except Exception as e:
                    logger.warning(f"Error obteniendo contexto RAG: {e}")
            
            # Construir prompt
            prompt = self._build_extraction_prompt(
                user_message,
                current_data,
                history,
                rag_context
            )
            
            # Llamar a Gemini con timeout
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 200
                }
            )
            
            # Parsear respuesta JSON
            response_text = response.text.strip()
            if response_text.startswith('```'):
                # Extraer JSON del bloque de código
                response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            
            # Parsear JSON
            llm_data = json.loads(response_text)
            
            # Usar datos del LLM como primarios
            extracted_data.update(llm_data)
            logger.info(f"✅ Datos extraídos con Gemini API: {llm_data}")
            
            # Si tenemos datos completos, retornar
            if 'rut' in extracted_data or 'motivo_consulta' in extracted_data:
                return extracted_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  Respuesta de Gemini no es JSON válido: {e}")
            logger.warning(f"Respuesta recibida: {response_text[:200] if 'response_text' in locals() else 'N/A'}")
        except Exception as e:
            logger.error(f"❌ Error en extracción con Gemini API: {e}")
        
        # FALLBACK: Extracción por regex si Gemini falla o no retorna datos completos
        logger.info("🔄 Usando regex como fallback...")
        regex_data = self._extract_data_with_regex(user_message, current_data)
        
        # Combinar datos (LLM tiene prioridad si existe, sino usar regex)
        for key, value in regex_data.items():
            if key not in extracted_data:
                extracted_data[key] = value
        
        if regex_data:
            logger.info(f"✅ Datos extraídos con regex (fallback): {regex_data}")
        
        # Si aún no tenemos datos, intentar extracción simple basada en keywords
        if not extracted_data.get('motivo_consulta'):
            motivo_simple = self._extract_simple_intent(user_message)
            if motivo_simple:
                extracted_data['motivo_consulta'] = motivo_simple
                logger.info(f"✅ Motivo extraído con análisis simple: {motivo_simple}")
        
        return extracted_data
    
    def _extract_data_with_regex(
        self,
        user_message: str,
        current_data: Dict
    ) -> Dict[str, Any]:
        """
        Extrae datos usando expresiones regulares (fallback confiable)
        
        Args:
            user_message: Mensaje del usuario
            current_data: Datos ya recolectados
            
        Returns:
            Dict con datos extraídos
        """
        extracted = {}
        message_lower = user_message.lower()
        
        # Extraer RUT con regex
        rut_pattern = r'\b(\d{7,8}[-\.]?\d)\b'
        rut_match = re.search(rut_pattern, user_message)
        if rut_match:
            rut = rut_match.group(1)
            # Normalizar formato (agregar guión si no lo tiene)
            if '-' not in rut and '.' not in rut:
                rut = f"{rut[:-1]}-{rut[-1]}"
            else:
                rut = rut.replace('.', '-')
            extracted['rut'] = rut
            logger.info(f"RUT extraído por regex: {rut}")
        
        # Extraer motivo de consulta por palabras clave
        motivos_keywords = {
            'consultar_monto': ['monto', 'pagar', 'pago', 'cuanto', 'cuánto', 'debo', 'valor', 'precio'],
            'consultar_consumo': ['consumo', 'gasto', 'metros', 'm3', 'm³', 'cuanto gaste', 'cuánto gaste'],
            'comparar_periodos': ['comparar', 'comparación', 'diferencia', 'meses', 'períodos', 'periodos'],
            'ver_boleta': ['ver', 'mostrar', 'boleta', 'factura', 'estado'],
            'estado_pago': ['estado', 'pagada', 'pendiente', 'vencida', 'pague', 'pagué']
        }
        
        # Buscar coincidencias
        max_matches = 0
        best_motivo = None
        
        for motivo, keywords in motivos_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            if matches > max_matches:
                max_matches = matches
                best_motivo = motivo
        
        if best_motivo:
            extracted['motivo_consulta'] = best_motivo
            logger.info(f"Motivo extraído por regex: {best_motivo}")
        
        # Detectar intención comparativa
        if any(word in message_lower for word in ['compar', 'diferen', 'meses', 'period']):
            extracted['quiere_comparar'] = True
        
        return extracted
    
    def _extract_simple_intent(self, user_message: str) -> Optional[str]:
        """
        Extrae intención simple cuando regex y LLM fallan
        Método ultra-simple basado en palabras clave principales
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Motivo de consulta o None
        """
        message_lower = user_message.lower()
        
        # Palabras clave prioritarias (más específicas primero)
        if any(word in message_lower for word in ['comparar', 'comparación', 'diferencia']):
            return 'comparar_periodos'
        
        if any(word in message_lower for word in ['consumo', 'gasto', 'metros', 'm3', 'm³']):
            return 'consultar_consumo'
        
        if any(word in message_lower for word in ['monto', 'pagar', 'cuanto debo', 'cuánto debo', 'valor', 'precio']):
            return 'consultar_monto'
        
        if any(word in message_lower for word in ['estado', 'pagada', 'pendiente', 'vencida']):
            return 'estado_pago'
        
        if any(word in message_lower for word in ['ver', 'mostrar', 'boleta', 'factura']):
            return 'ver_boleta'
        
        # Si menciona "boleta" o "consulta" de forma genérica
        if 'boleta' in message_lower or 'consulta' in message_lower:
            return 'ver_boleta'
        
        return None
    
    def _build_extraction_prompt(
        self,
        user_message: str,
        current_data: Dict,
        history: List[Dict],
        rag_context: str = ""
    ) -> str:
        """
        Construye el prompt para extracción de datos
        """
        history_text = "\n".join([
            f"{msg['rol']}: {msg['contenido']}"
            for msg in history
        ])
        current_data_text = json.dumps(current_data, indent=2, ensure_ascii=False)
        
        # Agregar contexto RAG si está disponible
        rag_section = ""
        if rag_context:
            rag_section = f"\n{rag_context}\n"
        
        prompt = f"""Eres un asistente especializado en consultas de boletas de agua potable.
{rag_section}
HISTORIAL DE CONVERSACIÓN:
{history_text}

DATOS YA RECOLECTADOS:
{current_data_text}

MENSAJE ACTUAL DEL USUARIO:
{user_message}

Tu tarea es extraer la siguiente información del mensaje del usuario:

1. **motivo_consulta**: Clasifica en uno de estos:
   - "ver_boleta": Quiere ver su boleta
   - "consultar_monto": Pregunta por el monto a pagar
   - "consultar_consumo": Pregunta por su consumo
   - "comparar_periodos": Quiere comparar boletas de diferentes períodos
   - "estado_pago": Pregunta por el estado de pago
   - "informacion_general": Consulta general
   - "otro": Otro tipo de consulta

2. **rut**: RUT del usuario en formato 12345678-9 (solo si lo menciona)

3. **periodo_interes**: Si menciona un período específico (formato YYYY-MM)

4. **quiere_comparar**: true si menciona comparar, false si no

INSTRUCCIONES:
- Solo extrae datos que estén EXPLÍCITAMENTE mencionados
- No inventes información
- El RUT debe tener formato chileno válido (con guión)
- Responde SOLO con un objeto JSON válido
- Si un dato no está presente, no lo incluyas en el JSON

Ejemplo de respuesta:
{{
  "motivo_consulta": "consultar_monto",
  "rut": "12345678-9"
}}

Responde SOLO con JSON:"""
        
        return prompt
    
    def _formatear_info_boleta(self, boleta: Boleta) -> str:
        """
        Formatea la información de una boleta para mostrar al usuario
        """
        estado_emoji = {
            'pendiente': '⏳',
            'pagada': '✅',
            'vencida': '⚠️',
            'anulada': '❌'
        }
        
        emoji = estado_emoji.get(boleta.estado_pago, '📄')
        consumo_text = f"{boleta.consumo} m³"
        
        info = (
            f"**Período:** {boleta.periodo_facturacion}\n"
            f"**Fecha Emisión:** {boleta.fecha_emision.strftime('%d/%m/%Y')}\n"
            f"**Fecha Vencimiento:** {boleta.fecha_vencimiento.strftime('%d/%m/%Y')}\n"
            f"**Consumo:** {consumo_text}\n"
            f"**Monto:** ${boleta.monto:,.0f}\n"
            f"**Estado:** {emoji} {boleta.get_estado_pago_display()}"
        )
        
        return info
    
    def _generar_comparacion(self, boletas: List[Boleta]) -> str:
        """
        Genera un análisis comparativo de boletas
        """
        if len(boletas) < 2:
            return "No hay suficientes boletas para comparar."
        
        mensaje = "📊 **Comparación de tus últimas boletas:**\n\n"
        
        # Mostrar cada boleta
        for i, boleta in enumerate(boletas[:3], 1):
            mensaje += f"**{i}. {boleta.periodo_facturacion}**\n"
            consumo_text = f"{boleta.consumo} m³"
            mensaje += f"   Consumo: {consumo_text}\n"
            mensaje += f"   Monto: ${boleta.monto:,.0f}\n"
            mensaje += f"   Estado: {boleta.get_estado_pago_display()}\n\n"
        
        # Análisis
        consumos = [float(b.consumo) for b in boletas[:3]]
        montos = [float(b.monto) for b in boletas[:3]]
        
        consumo_promedio = sum(consumos) / len(consumos)
        monto_promedio = sum(montos) / len(montos)
        
        # Variación del último período
        if len(consumos) >= 2:
            variacion_consumo = ((consumos[0] - consumos[1]) / consumos[1]) * 100
            
            mensaje += f"📈 **Análisis:**\n"
            consumo_prom_text = f"{consumo_promedio:.2f} m³"
            mensaje += f"   • Consumo promedio: {consumo_prom_text}\n"
            mensaje += f"   • Monto promedio: ${monto_promedio:,.0f}\n"
            
            if variacion_consumo > 10:
                mensaje += f"   • ⚠️ Tu consumo aumentó un {variacion_consumo:.1f}% respecto al período anterior\n"
            elif variacion_consumo < -10:
                mensaje += f"   • ✅ Tu consumo disminuyó un {abs(variacion_consumo):.1f}% respecto al período anterior\n"
            else:
                mensaje += f"   • ➡️ Tu consumo se mantiene estable\n"
        
        return mensaje
    
    def _generate_contextual_response(
        self,
        user_message: str,
        boleta: Boleta,
        conversation: ChatConversation
    ) -> str:
        """
        Genera una respuesta contextual usando Gemini con información de la boleta
        """
        # Información de la boleta para contexto
        consumo_m3 = f"{boleta.consumo} m³"
        boleta_context = (
            f"Información de la boleta del usuario:\n"
            f"- RUT: {boleta.rut}\n"
            f"- Nombre: {boleta.nombre}\n"
            f"- Período: {boleta.periodo_facturacion}\n"
            f"- Consumo: {consumo_m3}\n"
            f"- Monto: ${boleta.monto}\n"
            f"- Estado de pago: {boleta.get_estado_pago_display()}\n"
        )
        # Historial
        history = self._get_conversation_history(conversation, last_n=5)
        history_text = "\n".join([
            f"{msg['rol']}: {msg['contenido']}"
            for msg in history
        ])
        
        # Obtener contexto del RAG
        rag_context = ""
        if self.rag_retriever:
            try:
                rag_context = self.rag_retriever.get_relevant_context_text(
                    query=user_message,
                    max_length=1500
                )
            except Exception as e:
                logger.warning(f"Error obteniendo contexto RAG: {e}")
        
        prompt = f"""Eres un asistente virtual especializado en consultas de boletas de agua potable.
{rag_context}

{boleta_context}

HISTORIAL DE CONVERSACIÓN:
{history_text}

PREGUNTA DEL USUARIO:
{user_message}

Responde de manera clara, concisa y amigable. Si la pregunta está relacionada con la boleta, usa la información proporcionada. Si no tienes información específica, indícalo amablemente.

Responde en máximo 3-4 líneas:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generando respuesta contextual: {e}")
            return "Disculpa, tuve un problema procesando tu consulta. ¿Podrías reformular tu pregunta?"
    
    def _generate_comparative_analysis(
        self,
        user_message: str,
        boletas: List[Boleta],
        conversation: ChatConversation
    ) -> str:
        """
        Genera análisis comparativo usando Gemini
        """
        # Preparar datos de boletas
        boletas_data = []
        for boleta in boletas:
            boletas_data.append({
                'periodo': boleta.periodo_facturacion,
                'consumo': float(boleta.consumo),
                'monto': float(boleta.monto),
                'estado': boleta.estado_pago
            })
        
        boletas_json = json.dumps(boletas_data, indent=2, ensure_ascii=False)
        
        prompt = f"""Eres un asistente especializado en análisis de consumo de agua potable.

BOLETAS DEL USUARIO (últimos 6 períodos):
{boletas_json}

PREGUNTA DEL USUARIO:
{user_message}

Genera un análisis comparativo de las boletas. Incluye:
1. Tendencias de consumo (si aumenta, disminuye o se mantiene)
2. Variaciones significativas entre períodos
3. Recomendaciones si hay consumo excesivo
4. Respuesta específica a la pregunta del usuario

Formato de respuesta: Texto claro con emojis, máximo 8 líneas.

Responde:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generando análisis comparativo: {e}")
            return self._generar_comparacion(boletas)
    
    def _get_initial_message(self) -> str:
        """
        Mensaje inicial del chatbot
        """
        return (
            "¡Hola! 👋 Soy tu asistente virtual para consultas de boletas de agua potable.\n\n"
            "Puedo ayudarte con:\n"
            "• 📄 Ver tu boleta actual\n"
            "• 💵 Consultar montos y fechas de pago\n"
            "• 📊 Revisar tu consumo de agua\n"
            "• 📈 Comparar consumos entre diferentes períodos\n"
            "• ✅ Verificar el estado de pago\n\n"
            "¿En qué puedo ayudarte hoy?"
        )
    
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
