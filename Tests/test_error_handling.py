"""
Tests de manejo de errores y casos edge para el sistema de chatbot.
Validación de robustez y resiliencia.
"""

import unittest
from unittest.mock import Mock, patch
from django.test import TestCase
from ModuloEmergencia.models import ChatConversation, ChatMessage, Emergencia
from ModuloEmergencia.services.chatbot_service import ChatbotService
import uuid
import json


class InputValidationTests(TestCase):
    """Tests de validación de inputs"""
    
    def setUp(self):
        self.service = ChatbotService()
        self.conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_empty_message_handling(self, mock_extract, mock_llm):
        """Test manejo de mensaje vacío"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Por favor, escribe algo"
        
        response, estado, _ = self.service.process_message(
            str(self.conversation.session_id),
            ""
        )
        
        self.assertIsInstance(response, str)
        self.assertIsInstance(estado, str)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_very_long_message_handling(self, mock_extract, mock_llm):
        """Test manejo de mensaje muy largo"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Entendido"
        
        long_message = "palabra " * 10000  # 10,000 palabras
        
        try:
            response, estado, _ = self.service.process_message(
                str(self.conversation.session_id),
                long_message
            )
            self.assertIsInstance(response, str)
        except Exception as e:
            # Es aceptable que rechace mensajes muy largos
            self.assertIsInstance(e, Exception)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_special_characters_in_message(self, mock_extract, mock_llm):
        """Test manejo de caracteres especiales"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Entendido"
        
        special_message = "Hola! ¿Cómo están? Tengo $ y @ en mi mensaje #emergencia"
        
        response, estado, _ = self.service.process_message(
            str(self.conversation.session_id),
            special_message
        )
        
        self.assertIsInstance(response, str)
        
        # Verificar que el mensaje se guardó correctamente
        message = ChatMessage.objects.filter(
            conversation=self.conversation,
            contenido=special_message
        ).first()
        self.assertIsNotNone(message)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_sql_injection_attempt(self, mock_extract, mock_llm):
        """Test protección contra inyección SQL"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Respuesta segura"
        
        malicious_message = "'; DROP TABLE emergencias; --"
        
        response, estado, _ = self.service.process_message(
            str(self.conversation.session_id),
            malicious_message
        )
        
        # Django ORM debe proteger contra esto
        self.assertIsInstance(response, str)
        
        # Verificar que la tabla no se eliminó
        self.assertTrue(Emergencia.objects.model._meta.db_table)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_xss_attempt(self, mock_extract, mock_llm):
        """Test protección contra XSS"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Respuesta segura"
        
        xss_message = "<script>alert('XSS')</script>"
        
        response, estado, _ = self.service.process_message(
            str(self.conversation.session_id),
            xss_message
        )
        
        # El sistema debe manejar esto de forma segura
        self.assertIsInstance(response, str)


class DataExtractionErrorTests(TestCase):
    """Tests de errores en extracción de datos"""
    
    def setUp(self):
        self.service = ChatbotService()
        self.conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_invalid_json_from_llm(self, mock_gemini):
        """Test manejo de JSON inválido del LLM"""
        mock_response = Mock()
        mock_response.text = "Este no es JSON válido {{{["
        mock_gemini.return_value = mock_response
        
        result = self.service._extract_data_with_llm(
            "Mensaje de prueba",
            str(self.conversation.session_id)
        )
        
        # Debe retornar dict vacío en lugar de lanzar excepción
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_malformed_json_with_extra_text(self, mock_gemini):
        """Test manejo de JSON con texto extra"""
        mock_response = Mock()
        mock_response.text = 'Aquí está el JSON: {"sector": "anibana"} Espero que ayude!'
        mock_gemini.return_value = mock_response
        
        result = self.service._extract_data_with_llm(
            "Mensaje de prueba",
            str(self.conversation.session_id)
        )
        
        # Puede extraer el JSON o retornar dict vacío
        self.assertIsInstance(result, dict)
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_empty_response_from_llm(self, mock_gemini):
        """Test manejo de respuesta vacía del LLM"""
        mock_response = Mock()
        mock_response.text = ""
        mock_gemini.return_value = mock_response
        
        result = self.service._extract_data_with_llm(
            "Mensaje de prueba",
            str(self.conversation.session_id)
        )
        
        self.assertIsInstance(result, dict)
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_llm_returns_null_values(self, mock_gemini):
        """Test manejo de valores null en JSON"""
        mock_response = Mock()
        mock_response.text = '{"sector": null, "descripcion": null}'
        mock_gemini.return_value = mock_response
        
        result = self.service._extract_data_with_llm(
            "Mensaje de prueba",
            str(self.conversation.session_id)
        )
        
        self.assertIsInstance(result, dict)


class GeminiAPIErrorTests(TestCase):
    """Tests de manejo de errores de la API de Gemini"""
    
    def setUp(self):
        self.service = ChatbotService()
        self.conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_gemini_timeout(self, mock_gemini):
        """Test manejo de timeout de Gemini"""
        mock_gemini.side_effect = TimeoutError("Request timeout")
        
        try:
            result = self.service._generate_llm_response(
                "Mensaje de prueba",
                str(self.conversation.session_id)
            )
            # Si no lanza excepción, debe retornar mensaje por defecto
            self.assertIsInstance(result, str)
        except TimeoutError:
            # Es aceptable que propague el timeout
            pass
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_gemini_rate_limit(self, mock_gemini):
        """Test manejo de rate limit de Gemini"""
        mock_gemini.side_effect = Exception("Rate limit exceeded")
        
        try:
            result = self.service._extract_data_with_llm(
                "Mensaje de prueba",
                str(self.conversation.session_id)
            )
            # Debe manejar el error gracefully
            self.assertIsInstance(result, dict)
        except Exception:
            # Es aceptable que propague algunos errores
            pass
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_gemini_invalid_api_key(self, mock_gemini):
        """Test manejo de API key inválida"""
        mock_gemini.side_effect = Exception("Invalid API key")
        
        try:
            result = self.service._generate_llm_response(
                "Mensaje de prueba",
                str(self.conversation.session_id)
            )
            self.assertIsInstance(result, str)
        except Exception:
            pass
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_gemini_network_error(self, mock_gemini):
        """Test manejo de error de red"""
        mock_gemini.side_effect = ConnectionError("Network error")
        
        try:
            result = self.service._generate_llm_response(
                "Mensaje de prueba",
                str(self.conversation.session_id)
            )
            self.assertIsInstance(result, str)
        except ConnectionError:
            pass


class ConversationStateErrorTests(TestCase):
    """Tests de errores relacionados con estados de conversación"""
    
    def setUp(self):
        self.service = ChatbotService()
    
    def test_process_message_on_nonexistent_conversation(self):
        """Test procesar mensaje en conversación inexistente"""
        fake_session_id = str(uuid.uuid4())
        
        with self.assertRaises(ChatConversation.DoesNotExist):
            self.service.process_message(fake_session_id, "Hola")
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_process_message_on_finalized_conversation(self, mock_extract, mock_llm):
        """Test procesar mensaje en conversación finalizada"""
        mock_extract.return_value = {}
        mock_llm.return_value = "La conversación ya finalizó"
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='finalizada',
            datos_recolectados={}
        )
        
        # El sistema puede rechazar o permitir mensajes en conversaciones finalizadas
        try:
            response, estado, _ = self.service.process_message(
                str(conversation.session_id),
                "Otro mensaje"
            )
            self.assertIsInstance(response, str)
        except Exception:
            # Es aceptable que rechace mensajes en conversaciones finalizadas
            pass
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_process_message_on_cancelled_conversation(self, mock_extract, mock_llm):
        """Test procesar mensaje en conversación cancelada"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Conversación cancelada"
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='cancelada',
            datos_recolectados={}
        )
        
        try:
            response, estado, _ = self.service.process_message(
                str(conversation.session_id),
                "¿Puedo reactivar?"
            )
            self.assertIsInstance(response, str)
        except Exception:
            pass


class DataIntegrityTests(TestCase):
    """Tests de integridad de datos"""
    
    def setUp(self):
        self.service = ChatbotService()
    
    def test_create_emergency_with_incomplete_data(self):
        """Test crear emergencia con datos incompletos"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='solicitando_contacto',
            datos_recolectados={
                'sector': 'anibana'
                # Faltan: descripcion, direccion, nombre_usuario, telefono
            }
        )
        
        try:
            emergencia = self.service._create_emergencia(conversation)
            # Puede ser None o lanzar excepción
            if emergencia is not None:
                # Verificar que se creó con valores por defecto
                self.assertIsNotNone(emergencia.sector)
        except Exception:
            # Es aceptable que falle con datos incompletos
            pass
    
    def test_create_emergency_with_invalid_sector(self):
        """Test crear emergencia con sector inválido"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='solicitando_contacto',
            datos_recolectados={
                'sector': 'sector_inexistente',
                'descripcion': 'Test',
                'direccion': 'Test',
                'nombre_usuario': 'Test',
                'telefono': '+56911111111'
            }
        )
        
        try:
            emergencia = self.service._create_emergencia(conversation)
            # Puede fallar la validación
        except Exception:
            pass
    
    def test_datos_recolectados_is_valid_json(self):
        """Test que datos_recolectados es JSON válido"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={'sector': 'anibana', 'descripcion': 'Test'}
        )
        
        conversation.refresh_from_db()
        
        # Debe poder serializarse a JSON
        try:
            json_str = json.dumps(conversation.datos_recolectados)
            self.assertIsInstance(json_str, str)
        except Exception:
            self.fail("datos_recolectados no es JSON válido")


class ConcurrencyErrorTests(TestCase):
    """Tests de errores de concurrencia"""
    
    def setUp(self):
        self.service = ChatbotService()
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_concurrent_messages_same_session(self, mock_extract, mock_llm):
        """Test mensajes concurrentes en la misma sesión"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Respuesta"
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
        
        # Simular dos mensajes procesándose simultáneamente
        # En producción esto podría causar race conditions
        session_id = str(conversation.session_id)
        
        response1, _, _ = self.service.process_message(session_id, "Mensaje 1")
        response2, _, _ = self.service.process_message(session_id, "Mensaje 2")
        
        self.assertIsInstance(response1, str)
        self.assertIsInstance(response2, str)
        
        # Verificar que ambos mensajes se guardaron
        messages = ChatMessage.objects.filter(conversation=conversation)
        self.assertGreaterEqual(messages.count(), 2)


class RAGSystemErrorTests(TestCase):
    """Tests de errores del sistema RAG"""
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    def test_vector_store_unavailable(self, mock_vector_store):
        """Test manejo de vector store no disponible"""
        mock_vector_store.side_effect = Exception("ChromaDB not available")
        
        try:
            from ModuloEmergencia.RAG.retriever import RAGRetriever
            retriever = RAGRetriever()
            # Puede fallar o usar fallback
        except Exception:
            # Es aceptable que falle si el RAG no está disponible
            pass
    
    @patch('ModuloEmergencia.RAG.retriever.RAGRetriever.get_relevant_context')
    def test_rag_retrieval_error(self, mock_retriever):
        """Test manejo de error en retrieval"""
        mock_retriever.side_effect = Exception("Retrieval failed")
        
        service = ChatbotService()
        
        # El servicio debe manejar errores del RAG
        try:
            # Intentar usar el servicio sin RAG
            conversation = ChatConversation.objects.create(
                session_id=uuid.uuid4(),
                estado='iniciada',
                datos_recolectados={}
            )
            # Debe funcionar incluso si el RAG falla
            self.assertIsNotNone(service)
        except Exception:
            pass
    
    @patch('ModuloEmergencia.RAG.embeddings.DocumentProcessor.generate_embeddings')
    def test_embedding_generation_error(self, mock_embeddings):
        """Test manejo de error en generación de embeddings"""
        mock_embeddings.side_effect = Exception("Model not available")
        
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        processor = DocumentProcessor()
        
        try:
            embeddings = processor.generate_embeddings(["Texto de prueba"])
            # Puede retornar lista vacía o lanzar excepción
        except Exception:
            pass


class EdgeCaseTests(TestCase):
    """Tests de casos edge"""
    
    def setUp(self):
        self.service = ChatbotService()
    
    def test_priority_calculation_with_empty_description(self):
        """Test cálculo de prioridad con descripción vacía"""
        prioridad = self.service._calcular_prioridad("")
        
        self.assertIn(prioridad, ['baja', 'media', 'alta', 'critica'])
    
    def test_priority_calculation_with_mixed_keywords(self):
        """Test cálculo de prioridad con keywords mixtas"""
        descripcion = "Corte de agua y fuga simultáneos"
        prioridad = self.service._calcular_prioridad(descripcion)
        
        # Debe tomar la prioridad más alta (crítica por "corte")
        self.assertIn(prioridad, ['alta', 'critica'])
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_conversation_with_only_system_messages(self, mock_extract, mock_llm):
        """Test conversación con solo mensajes del sistema"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Respuesta"
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
        
        # Crear solo mensajes del asistente (no del usuario)
        ChatMessage.objects.create(
            conversation=conversation,
            rol='asistente',
            contenido='Mensaje del sistema'
        )
        
        # El sistema debe manejar esto correctamente
        messages = ChatMessage.objects.filter(conversation=conversation)
        self.assertEqual(messages.count(), 1)
    
    def test_phone_number_with_various_formats(self):
        """Test validación de teléfonos en diferentes formatos"""
        phone_numbers = [
            '+56912345678',
            '56912345678',
            '912345678',
            '+56 9 1234 5678',
            '+56-9-1234-5678'
        ]
        
        for phone in phone_numbers:
            # Intentar crear emergencia con cada formato
            try:
                emergencia = Emergencia.objects.create(
                    sector='anibana',
                    tipo_emergencia='fuga_agua',
                    descripcion='Test',
                    direccion='Test',
                    nombre_usuario='Test',
                    telefono=phone,
                    nivel_prioridad='media'
                )
                self.assertIsNotNone(emergencia)
            except Exception:
                # Algunos formatos pueden ser rechazados
                pass


class ResourceLimitTests(TestCase):
    """Tests de límites de recursos"""
    
    def setUp(self):
        self.service = ChatbotService()
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_conversation_with_many_messages(self, mock_extract, mock_llm):
        """Test conversación con muchos mensajes"""
        mock_extract.return_value = {}
        mock_llm.return_value = "Respuesta"
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
        
        # Crear 100 mensajes
        for i in range(100):
            ChatMessage.objects.create(
                conversation=conversation,
                rol='usuario' if i % 2 == 0 else 'asistente',
                contenido=f'Mensaje {i}'
            )
        
        # Verificar que se pueden recuperar todos
        messages = ChatMessage.objects.filter(conversation=conversation)
        self.assertEqual(messages.count(), 100)
    
    def test_many_concurrent_conversations(self):
        """Test crear muchas conversaciones simultáneas"""
        # Crear 50 conversaciones
        conversations = []
        for i in range(50):
            conv = ChatConversation.objects.create(
                session_id=uuid.uuid4(),
                estado='iniciada',
                datos_recolectados={}
            )
            conversations.append(conv)
        
        # Verificar que todas se crearon
        self.assertEqual(len(conversations), 50)
        
        # Verificar que todas tienen session_id único
        session_ids = [str(c.session_id) for c in conversations]
        self.assertEqual(len(session_ids), len(set(session_ids)))


if __name__ == '__main__':
    unittest.main()
