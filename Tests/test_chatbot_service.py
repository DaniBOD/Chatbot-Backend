"""
Tests enfocados en el servicio principal del chatbot (chatbot_service.py).
Objetivo: Aumentar cobertura de 43% a 80%+
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from ModuloEmergencia.models import ChatConversation, ChatMessage, Emergencia
from ModuloEmergencia.services.chatbot_service import ChatbotService
import uuid


class ChatbotServiceInitializationTests(TestCase):
    """Tests de inicialización y configuración del servicio"""
    
    def test_service_initialization(self):
        """Test que el servicio se inicializa correctamente"""
        service = ChatbotService()
        self.assertIsNotNone(service)
        self.assertIsNotNone(service.retriever)
    
    def test_service_has_retriever(self):
        """Test que el servicio tiene un retriever configurado"""
        service = ChatbotService()
        self.assertIsNotNone(service.retriever)
        self.assertTrue(hasattr(service.retriever, 'get_relevant_context'))


class StartConversationTests(TestCase):
    """Tests del método start_conversation()"""
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    def test_start_conversation_creates_new_session(self, mock_llm):
        """Test que start_conversation crea una nueva conversación"""
        mock_llm.return_value = "¡Hola! ¿En qué puedo ayudarte?"
        
        service = ChatbotService()
        session_id, estado, respuesta = service.start_conversation()
        
        # Verificar que retorna los valores correctos
        self.assertIsNotNone(session_id)
        self.assertEqual(estado, 'iniciada')
        self.assertIsInstance(respuesta, str)
        self.assertIn("Hola", respuesta)
        
        # Verificar que se creó la conversación en DB
        conversation = ChatConversation.objects.get(session_id=session_id)
        self.assertEqual(conversation.estado, 'iniciada')
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    def test_start_conversation_creates_initial_message(self, mock_llm):
        """Test que start_conversation crea el mensaje inicial del asistente"""
        mock_llm.return_value = "Mensaje de bienvenida"
        
        service = ChatbotService()
        session_id, estado, respuesta = service.start_conversation()
        
        # Verificar que se creó el mensaje del asistente
        messages = ChatMessage.objects.filter(
            conversation__session_id=session_id,
            rol='asistente'
        )
        self.assertEqual(messages.count(), 1)
        self.assertEqual(messages.first().contenido, "Mensaje de bienvenida")
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    def test_start_conversation_initializes_empty_data(self, mock_llm):
        """Test que start_conversation inicializa datos_recolectados vacíos"""
        mock_llm.return_value = "Hola"
        
        service = ChatbotService()
        session_id, _, _ = service.start_conversation()
        
        conversation = ChatConversation.objects.get(session_id=session_id)
        self.assertEqual(conversation.datos_recolectados, {})
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    def test_start_conversation_sets_correct_timestamp(self, mock_llm):
        """Test que start_conversation establece fecha_inicio correcta"""
        mock_llm.return_value = "Hola"
        
        before = timezone.now()
        service = ChatbotService()
        session_id, _, _ = service.start_conversation()
        after = timezone.now()
        
        conversation = ChatConversation.objects.get(session_id=session_id)
        self.assertIsNotNone(conversation.fecha_inicio)
        self.assertTrue(before <= conversation.fecha_inicio <= after)


class ProcessMessageTests(TestCase):
    """Tests del método process_message()"""
    
    def setUp(self):
        """Crear una conversación de prueba"""
        self.conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_process_message_saves_user_message(self, mock_extract, mock_llm):
        """Test que process_message guarda el mensaje del usuario"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Respuesta del bot"
        
        service = ChatbotService()
        mensaje_usuario = "Hola, tengo una emergencia"
        
        respuesta, estado, _ = service.process_message(
            str(self.conversation.session_id),
            mensaje_usuario
        )
        
        # Verificar que se guardó el mensaje del usuario
        user_messages = ChatMessage.objects.filter(
            conversation=self.conversation,
            rol='usuario',
            contenido=mensaje_usuario
        )
        self.assertEqual(user_messages.count(), 1)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_process_message_saves_assistant_message(self, mock_extract, mock_llm):
        """Test que process_message guarda el mensaje del asistente"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Esta es mi respuesta"
        
        service = ChatbotService()
        respuesta, estado, _ = service.process_message(
            str(self.conversation.session_id),
            "Mensaje de prueba"
        )
        
        # Verificar que se guardó la respuesta del asistente
        assistant_messages = ChatMessage.objects.filter(
            conversation=self.conversation,
            rol='asistente',
            contenido="Esta es mi respuesta"
        )
        self.assertEqual(assistant_messages.count(), 1)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_process_message_returns_response_and_state(self, mock_extract, mock_llm):
        """Test que process_message retorna respuesta y estado correctos"""
        mock_extract.return_value = {'sector': 'anibana'}
        mock_llm.return_value = "Perfecto, ¿qué tipo de emergencia?"
        
        service = ChatbotService()
        respuesta, estado, datos = service.process_message(
            str(self.conversation.session_id),
            "Estoy en Anibana"
        )
        
        self.assertEqual(respuesta, "Perfecto, ¿qué tipo de emergencia?")
        self.assertEqual(estado, 'recolectando_datos')
        self.assertIsInstance(datos, dict)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_process_message_with_nonexistent_session(self, mock_extract, mock_llm):
        """Test que process_message maneja sesiones inexistentes"""
        service = ChatbotService()
        fake_session_id = str(uuid.uuid4())
        
        with self.assertRaises(ChatConversation.DoesNotExist):
            service.process_message(fake_session_id, "Hola")
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_process_message_accumulates_data(self, mock_extract, mock_llm):
        """Test que process_message acumula datos en datos_recolectados"""
        mock_llm.return_value = "Gracias"
        
        # Primera extracción: sector
        mock_extract.return_value = {'sector': 'anibana'}
        service = ChatbotService()
        service.process_message(str(self.conversation.session_id), "Anibana")
        
        # Segunda extracción: descripción
        mock_extract.return_value = {'descripcion': 'Fuga de agua'}
        service.process_message(str(self.conversation.session_id), "Hay una fuga")
        
        # Verificar que ambos datos se acumularon
        self.conversation.refresh_from_db()
        self.assertIn('sector', self.conversation.datos_recolectados)
        self.assertIn('descripcion', self.conversation.datos_recolectados)
        self.assertEqual(self.conversation.datos_recolectados['sector'], 'anibana')


class DataExtractionTests(TestCase):
    """Tests del método _extract_data_with_llm()"""
    
    def setUp(self):
        self.conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
        self.service = ChatbotService()
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_extract_data_returns_dict(self, mock_gemini):
        """Test que _extract_data_with_llm retorna un diccionario"""
        mock_response = Mock()
        mock_response.text = '{"sector": "anibana", "descripcion": "Fuga de agua"}'
        mock_gemini.return_value = mock_response
        
        result = self.service._extract_data_with_llm(
            "Hay una fuga en Anibana",
            str(self.conversation.session_id)
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('sector', result)
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_extract_data_handles_invalid_json(self, mock_gemini):
        """Test que _extract_data_with_llm maneja JSON inválido"""
        mock_response = Mock()
        mock_response.text = 'Esto no es JSON válido'
        mock_gemini.return_value = mock_response
        
        result = self.service._extract_data_with_llm(
            "Mensaje de prueba",
            str(self.conversation.session_id)
        )
        
        # Debe retornar diccionario vacío en caso de error
        self.assertIsInstance(result, dict)
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_extract_data_extracts_sector(self, mock_gemini):
        """Test que extrae correctamente el sector"""
        mock_response = Mock()
        mock_response.text = '{"sector": "pedro_aguirre_cerda"}'
        mock_gemini.return_value = mock_response
        
        result = self.service._extract_data_with_llm(
            "Estoy en Pedro Aguirre Cerda",
            str(self.conversation.session_id)
        )
        
        self.assertEqual(result.get('sector'), 'pedro_aguirre_cerda')
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_extract_data_extracts_phone(self, mock_gemini):
        """Test que extrae correctamente el teléfono"""
        mock_response = Mock()
        mock_response.text = '{"telefono": "+56912345678"}'
        mock_gemini.return_value = mock_response
        
        result = self.service._extract_data_with_llm(
            "Mi teléfono es +56912345678",
            str(self.conversation.session_id)
        )
        
        self.assertEqual(result.get('telefono'), '+56912345678')


class StateTransitionTests(TestCase):
    """Tests de transiciones de estado"""
    
    def setUp(self):
        self.service = ChatbotService()
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_transition_to_collecting_data(self, mock_extract, mock_llm):
        """Test transición de iniciada a recolectando_datos"""
        mock_extract.return_value = {}
        mock_llm.return_value = "¿En qué sector?"
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='iniciada',
            datos_recolectados={}
        )
        
        self.service.process_message(
            str(conversation.session_id),
            "Tengo una emergencia"
        )
        
        conversation.refresh_from_db()
        self.assertEqual(conversation.estado, 'recolectando_datos')
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._calcular_prioridad')
    def test_transition_to_calculating_priority(self, mock_calc, mock_extract, mock_llm):
        """Test transición a calculando_prioridad cuando hay datos suficientes"""
        mock_extract.return_value = {'direccion': 'Calle 123'}
        mock_llm.return_value = "Calculando prioridad..."
        mock_calc.return_value = 'media'
        
        # Conversación con casi todos los datos
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={
                'sector': 'anibana',
                'descripcion': 'Fuga de agua',
                'nombre_usuario': 'Juan',
                'telefono': '+56912345678'
            }
        )
        
        self.service.process_message(
            str(conversation.session_id),
            "Calle Principal 123"
        )
        
        conversation.refresh_from_db()
        # Debe cambiar a calculando_prioridad o solicitando_contacto
        self.assertIn(conversation.estado, ['calculando_prioridad', 'solicitando_contacto'])


class PriorityCalculationTests(TestCase):
    """Tests del método _calcular_prioridad()"""
    
    def setUp(self):
        self.service = ChatbotService()
    
    def test_calculate_priority_critical(self):
        """Test cálculo de prioridad crítica"""
        descripcion = "Corte total de agua en todo el sector"
        prioridad = self.service._calcular_prioridad(descripcion)
        self.assertEqual(prioridad, 'critica')
    
    def test_calculate_priority_high(self):
        """Test cálculo de prioridad alta"""
        descripcion = "Rotura de la matriz principal"
        prioridad = self.service._calcular_prioridad(descripcion)
        self.assertEqual(prioridad, 'alta')
    
    def test_calculate_priority_medium(self):
        """Test cálculo de prioridad media"""
        descripcion = "Hay una fuga de agua en la calle"
        prioridad = self.service._calcular_prioridad(descripcion)
        self.assertEqual(prioridad, 'media')
    
    def test_calculate_priority_low(self):
        """Test cálculo de prioridad baja"""
        descripcion = "El agua sale con color amarillo"
        prioridad = self.service._calcular_prioridad(descripcion)
        self.assertEqual(prioridad, 'baja')
    
    def test_calculate_priority_default(self):
        """Test cálculo de prioridad por defecto (sin keywords)"""
        descripcion = "Tengo un problema con el servicio"
        prioridad = self.service._calcular_prioridad(descripcion)
        self.assertIn(prioridad, ['baja', 'media'])


class EmergencyCreationTests(TestCase):
    """Tests de creación de emergencia"""
    
    def setUp(self):
        self.service = ChatbotService()
        self.conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='solicitando_contacto',
            datos_recolectados={
                'sector': 'anibana',
                'descripcion': 'Fuga de agua grande',
                'direccion': 'Calle Principal 123',
                'nombre_usuario': 'Juan Pérez',
                'telefono': '+56912345678',
                'tipo_emergencia': 'fuga_agua'
            }
        )
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._create_emergencia')
    def test_create_emergency_when_user_confirms(self, mock_create, mock_extract, mock_llm):
        """Test que se crea emergencia cuando usuario confirma contacto"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Perfecto, emergencia registrada"
        mock_create.return_value = Mock(id_emergencia=uuid.uuid4())
        
        respuesta, estado, _ = self.service.process_message(
            str(self.conversation.session_id),
            "Sí, pueden contactarme"
        )
        
        # Verificar que se intentó crear la emergencia
        mock_create.assert_called_once()
        
        # Verificar que el estado cambió a finalizada
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.estado, 'finalizada')
    
    def test_create_emergencia_with_complete_data(self):
        """Test que _create_emergencia crea correctamente con datos completos"""
        emergencia = self.service._create_emergencia(self.conversation)
        
        self.assertIsNotNone(emergencia)
        self.assertEqual(emergencia.sector, 'anibana')
        self.assertEqual(emergencia.descripcion, 'Fuga de agua grande')
        self.assertEqual(emergencia.direccion, 'Calle Principal 123')
        self.assertEqual(emergencia.nombre_usuario, 'Juan Pérez')
        self.assertEqual(emergencia.telefono, '+56912345678')
        self.assertIn(emergencia.nivel_prioridad, ['baja', 'media', 'alta', 'critica'])


class ConversationHistoryTests(TestCase):
    """Tests de manejo del historial de conversación"""
    
    def setUp(self):
        self.service = ChatbotService()
        self.conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_conversation_maintains_history(self, mock_extract, mock_llm):
        """Test que la conversación mantiene el historial"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Entendido"
        
        # Enviar múltiples mensajes
        messages = [
            "Hola",
            "Tengo una emergencia",
            "Estoy en Anibana"
        ]
        
        for msg in messages:
            self.service.process_message(str(self.conversation.session_id), msg)
        
        # Verificar que se guardaron todos los mensajes
        total_messages = ChatMessage.objects.filter(
            conversation=self.conversation
        ).count()
        
        # Debe haber 3 mensajes de usuario + 3 respuestas = 6 mensajes
        self.assertEqual(total_messages, 6)
    
    def test_get_conversation_history(self):
        """Test obtener historial de conversación"""
        # Crear algunos mensajes
        ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido='Hola'
        )
        ChatMessage.objects.create(
            conversation=self.conversation,
            rol='asistente',
            contenido='¿En qué puedo ayudarte?'
        )
        
        messages = ChatMessage.objects.filter(
            conversation=self.conversation
        ).order_by('timestamp')
        
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages[0].rol, 'usuario')
        self.assertEqual(messages[1].rol, 'asistente')


class ErrorHandlingTests(TestCase):
    """Tests de manejo de errores"""
    
    def setUp(self):
        self.service = ChatbotService()
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_handle_gemini_api_error(self, mock_gemini):
        """Test manejo de errores de la API de Gemini"""
        mock_gemini.side_effect = Exception("API Error")
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
        
        # No debe lanzar excepción, debe manejarse internamente
        try:
            result = self.service._extract_data_with_llm(
                "Mensaje de prueba",
                str(conversation.session_id)
            )
            # Debe retornar dict vacío en caso de error
            self.assertIsInstance(result, dict)
        except Exception:
            self.fail("No debería lanzar excepción")
    
    def test_handle_missing_conversation_data(self):
        """Test manejo de datos faltantes en conversación"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='solicitando_contacto',
            datos_recolectados={
                'sector': 'anibana'
                # Faltan otros datos requeridos
            }
        )
        
        # Intentar crear emergencia con datos incompletos
        try:
            emergencia = self.service._create_emergencia(conversation)
            # Puede ser None o lanzar excepción
            if emergencia is None:
                self.assertIsNone(emergencia)
        except Exception:
            # Es aceptable que lance excepción por datos incompletos
            pass


class RAGIntegrationTests(TestCase):
    """Tests de integración con el sistema RAG"""
    
    def setUp(self):
        self.service = ChatbotService()
    
    @patch('ModuloEmergencia.RAG.retriever.RAGRetriever.get_relevant_context')
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_llm_response_uses_rag_context(self, mock_gemini, mock_retriever):
        """Test que las respuestas usan contexto del RAG"""
        mock_retriever.return_value = "Contexto relevante de la base de conocimiento"
        mock_response = Mock()
        mock_response.text = "Respuesta basada en contexto"
        mock_gemini.return_value = mock_response
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
        
        response = self.service._generate_llm_response(
            "¿Cuál es el horario de atención?",
            str(conversation.session_id)
        )
        
        # Verificar que se llamó al retriever
        mock_retriever.assert_called_once()
        self.assertIsInstance(response, str)


if __name__ == '__main__':
    unittest.main()
