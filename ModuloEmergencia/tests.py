"""
Tests unitarios para el Módulo de Emergencias
"""
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
import uuid

from ModuloEmergencia.models import Emergencia, ChatConversation, ChatMessage
from ModuloEmergencia.services.chatbot_service import ChatbotService


class EmergenciaModelTests(TestCase):
    """Tests para el modelo Emergencia"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.emergencia_data = {
            'sector': 'pedro_aguirre_cerda',
            'tipo_emergencia': 'fuga_agua',
            'prioridad': 'alta',
            'descripcion': 'Fuga grande en la calle',
            'direccion': 'Calle Principal 123',
            'nombre_usuario': 'Juan Pérez',
            'telefono': '+56912345678',
            'estado': 'reportada'
        }

    def test_crear_emergencia(self):
        """Test: Crear emergencia con datos válidos"""
        emergencia = Emergencia.objects.create(**self.emergencia_data)
        
        self.assertIsNotNone(emergencia.id_emergencia)
        self.assertEqual(emergencia.sector, 'pedro_aguirre_cerda')
        self.assertEqual(emergencia.tipo_emergencia, 'fuga_agua')
        self.assertEqual(emergencia.prioridad, 'alta')
        self.assertEqual(emergencia.estado, 'reportada')

    def test_emergencia_str_representation(self):
        """Test: Representación en string de la emergencia"""
        emergencia = Emergencia.objects.create(**self.emergencia_data)
        expected = f"Emergencia {emergencia.id_emergencia} - fuga_agua (alta)"
        self.assertEqual(str(emergencia), expected)

    def test_calcular_prioridad_alta(self):
        """Test: Cálculo de prioridad ALTA"""
        emergencia = Emergencia.objects.create(
            sector='pedro_aguirre_cerda',
            tipo_emergencia='corte_suministro',
            descripcion='Corte total de agua',
            direccion='Calle 123',
            nombre_usuario='Test',
            telefono='123456789'
        )
        emergencia.calcular_prioridad()
        self.assertEqual(emergencia.prioridad, 'alta')

    def test_calcular_prioridad_media(self):
        """Test: Cálculo de prioridad MEDIA"""
        emergencia = Emergencia.objects.create(
            sector='pedro_aguirre_cerda',
            tipo_emergencia='fuga_agua',
            descripcion='Fuga pequeña',
            direccion='Calle 456',
            nombre_usuario='Test',
            telefono='123456789'
        )
        emergencia.calcular_prioridad()
        self.assertEqual(emergencia.prioridad, 'media')

    def test_emergencia_con_fotografia(self):
        """Test: Emergencia puede tener fotografía (campo opcional)"""
        emergencia = Emergencia.objects.create(
            **self.emergencia_data,
            fotografia='path/to/photo.jpg'
        )
        self.assertEqual(emergencia.fotografia, 'path/to/photo.jpg')


class ChatConversationModelTests(TestCase):
    """Tests para el modelo ChatConversation"""

    def test_crear_conversacion(self):
        """Test: Crear conversación de chat"""
        session_id = str(uuid.uuid4())
        conversation = ChatConversation.objects.create(
            session_id=session_id,
            estado='iniciada'
        )
        
        self.assertEqual(conversation.session_id, session_id)
        self.assertEqual(conversation.estado, 'iniciada')
        self.assertIsNotNone(conversation.fecha_inicio)
        self.assertEqual(conversation.datos_recolectados, {})

    def test_conversacion_con_datos_recolectados(self):
        """Test: Conversación puede almacenar datos recolectados"""
        datos = {
            'sector': 'pedro_aguirre_cerda',
            'nombre_usuario': 'Test User',
            'telefono': '123456789'
        }
        conversation = ChatConversation.objects.create(
            session_id=str(uuid.uuid4()),
            estado='recolectando_datos',
            datos_recolectados=datos
        )
        
        self.assertEqual(conversation.datos_recolectados['sector'], 'pedro_aguirre_cerda')
        self.assertEqual(conversation.datos_recolectados['nombre_usuario'], 'Test User')

    def test_conversacion_puede_tener_emergencia(self):
        """Test: Conversación puede estar asociada a una emergencia"""
        emergencia = Emergencia.objects.create(
            sector='pedro_aguirre_cerda',
            tipo_emergencia='fuga_agua',
            descripcion='Test',
            direccion='Test 123',
            nombre_usuario='Test',
            telefono='123456789'
        )
        
        conversation = ChatConversation.objects.create(
            session_id=str(uuid.uuid4()),
            estado='finalizada',
            emergencia=emergencia
        )
        
        self.assertEqual(conversation.emergencia, emergencia)


class ChatMessageModelTests(TestCase):
    """Tests para el modelo ChatMessage"""

    def setUp(self):
        """Configuración inicial"""
        self.conversation = ChatConversation.objects.create(
            session_id=str(uuid.uuid4()),
            estado='iniciada'
        )

    def test_crear_mensaje_usuario(self):
        """Test: Crear mensaje de usuario"""
        mensaje = ChatMessage.objects.create(
            conversacion=self.conversation,
            rol='usuario',
            contenido='Hola, tengo una emergencia'
        )
        
        self.assertEqual(mensaje.rol, 'usuario')
        self.assertEqual(mensaje.contenido, 'Hola, tengo una emergencia')
        self.assertEqual(mensaje.conversacion, self.conversation)

    def test_crear_mensaje_asistente(self):
        """Test: Crear mensaje del asistente"""
        mensaje = ChatMessage.objects.create(
            conversacion=self.conversation,
            rol='asistente',
            contenido='¿En qué sector se encuentra?'
        )
        
        self.assertEqual(mensaje.rol, 'asistente')
        self.assertIsNotNone(mensaje.timestamp)

    def test_mensaje_str_representation(self):
        """Test: Representación en string del mensaje"""
        mensaje = ChatMessage.objects.create(
            conversacion=self.conversation,
            rol='usuario',
            contenido='Test mensaje'
        )
        expected = f"Mensaje {mensaje.id} - usuario"
        self.assertEqual(str(mensaje), expected)


class ChatbotServiceTests(TestCase):
    """Tests para ChatbotService"""

    def setUp(self):
        """Configuración inicial"""
        self.session_id = str(uuid.uuid4())

    @patch('ModuloEmergencia.services.chatbot_service.genai')
    @patch('ModuloEmergencia.services.chatbot_service.get_rag_retriever')
    def test_start_conversation(self, mock_rag, mock_genai):
        """Test: Iniciar nueva conversación"""
        # Mock del RAG retriever
        mock_rag.return_value = Mock()
        
        # Mock de Gemini
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        service = ChatbotService()
        conversation, message = service.start_conversation(self.session_id)
        
        self.assertEqual(conversation.session_id, self.session_id)
        self.assertEqual(conversation.estado, 'iniciada')
        self.assertIn('Hola', message)
        self.assertIn('asistente virtual', message.lower())

    @patch('ModuloEmergencia.services.chatbot_service.genai')
    @patch('ModuloEmergencia.services.chatbot_service.get_rag_retriever')
    def test_process_message_inicial(self, mock_rag, mock_genai):
        """Test: Procesar primer mensaje del usuario"""
        # Setup mocks
        mock_rag_instance = Mock()
        mock_rag_instance.get_relevant_context_text.return_value = "Contexto de prueba"
        mock_rag.return_value = mock_rag_instance
        
        mock_response = Mock()
        mock_response.text = json.dumps({
            "sector": "pedro_aguirre_cerda",
            "tipo_emergencia": "fuga_agua"
        })
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Crear conversación
        conversation = ChatConversation.objects.create(
            session_id=self.session_id,
            estado='iniciada'
        )
        
        service = ChatbotService()
        response, estado = service.process_message(
            self.session_id,
            "Tengo una fuga de agua en Pedro Aguirre Cerda"
        )
        
        self.assertIsNotNone(response)
        conversation.refresh_from_db()
        self.assertEqual(conversation.estado, 'recolectando_datos')


class ChatAPITests(APITestCase):
    """Tests para los endpoints de la API"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
        self.init_url = reverse('chat-init')

    @patch('ModuloEmergencia.views.get_chatbot_service')
    def test_init_chat_success(self, mock_service):
        """Test: Iniciar chat exitosamente"""
        session_id = str(uuid.uuid4())
        mock_conversation = Mock()
        mock_conversation.session_id = session_id
        mock_conversation.estado = 'iniciada'
        
        mock_service_instance = Mock()
        mock_service_instance.start_conversation.return_value = (
            mock_conversation,
            "Hola, soy el asistente"
        )
        mock_service.return_value = mock_service_instance
        
        response = self.client.post(self.init_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['estado'], 'iniciada')

    def test_init_chat_creates_conversation(self):
        """Test: Init chat crea conversación en BD (integración)"""
        with patch('ModuloEmergencia.services.chatbot_service.genai'):
            with patch('ModuloEmergencia.services.chatbot_service.get_rag_retriever'):
                response = self.client.post(self.init_url, {}, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                session_id = response.data['session_id']
                
                # Verificar que existe en BD
                conversation = ChatConversation.objects.get(session_id=session_id)
                self.assertEqual(conversation.estado, 'iniciada')

    @patch('ModuloEmergencia.views.get_chatbot_service')
    def test_chat_message_success(self, mock_service):
        """Test: Enviar mensaje exitosamente"""
        session_id = str(uuid.uuid4())
        
        # Crear conversación real
        ChatConversation.objects.create(
            session_id=session_id,
            estado='iniciada'
        )
        
        mock_service_instance = Mock()
        mock_service_instance.process_message.return_value = (
            "Entendido, ¿en qué sector?",
            "recolectando_datos"
        )
        mock_service.return_value = mock_service_instance
        
        response = self.client.post(
            reverse('chat-message'),
            {
                'session_id': session_id,
                'message': 'Tengo una emergencia'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('response', response.data)
        self.assertEqual(response.data['estado'], 'recolectando_datos')

    def test_chat_message_missing_session_id(self):
        """Test: Enviar mensaje sin session_id retorna error"""
        response = self.client.post(
            reverse('chat-message'),
            {'message': 'Hola'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_message_invalid_session_id(self):
        """Test: Session ID inválido retorna error"""
        response = self.client.post(
            reverse('chat-message'),
            {
                'session_id': str(uuid.uuid4()),
                'message': 'Hola'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EmergenciaViewSetTests(APITestCase):
    """Tests para EmergenciaViewSet"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
        self.list_url = reverse('emergencia-list')

    def test_list_emergencias(self):
        """Test: Listar emergencias"""
        # Crear emergencias de prueba
        Emergencia.objects.create(
            sector='pedro_aguirre_cerda',
            tipo_emergencia='fuga_agua',
            descripcion='Test 1',
            direccion='Calle 1',
            nombre_usuario='User 1',
            telefono='111111111',
            prioridad='alta'
        )
        Emergencia.objects.create(
            sector='san_jose_de_maipo',
            tipo_emergencia='corte_suministro',
            descripcion='Test 2',
            direccion='Calle 2',
            nombre_usuario='User 2',
            telefono='222222222',
            prioridad='media'
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_emergencias_by_sector(self):
        """Test: Filtrar emergencias por sector"""
        Emergencia.objects.create(
            sector='pedro_aguirre_cerda',
            tipo_emergencia='fuga_agua',
            descripcion='Test',
            direccion='Calle 1',
            nombre_usuario='User',
            telefono='111111111'
        )
        
        response = self.client.get(
            self.list_url,
            {'sector': 'pedro_aguirre_cerda'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_emergencias_by_prioridad(self):
        """Test: Filtrar emergencias por prioridad"""
        Emergencia.objects.create(
            sector='pedro_aguirre_cerda',
            tipo_emergencia='corte_suministro',
            descripcion='Urgente',
            direccion='Calle 1',
            nombre_usuario='User',
            telefono='111111111',
            prioridad='alta'
        )
        
        response = self.client.get(
            self.list_url,
            {'prioridad': 'alta'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) >= 1)

    def test_retrieve_emergencia(self):
        """Test: Obtener detalle de emergencia"""
        emergencia = Emergencia.objects.create(
            sector='pedro_aguirre_cerda',
            tipo_emergencia='fuga_agua',
            descripcion='Test detalle',
            direccion='Calle Test',
            nombre_usuario='Test User',
            telefono='123456789'
        )
        
        url = reverse('emergencia-detail', kwargs={'pk': emergencia.id_emergencia})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['descripcion'], 'Test detalle')


class IntegrationTests(APITestCase):
    """Tests de integración end-to-end"""

    @patch('ModuloEmergencia.services.chatbot_service.genai')
    @patch('ModuloEmergencia.services.chatbot_service.get_rag_retriever')
    def test_flujo_completo_chat(self, mock_rag, mock_genai):
        """Test: Flujo completo de conversación hasta crear emergencia"""
        # Setup mocks
        mock_rag_instance = Mock()
        mock_rag_instance.get_relevant_context_text.return_value = "Contexto"
        mock_rag.return_value = mock_rag_instance
        
        # Mock respuestas de Gemini
        responses = [
            json.dumps({
                "sector": "pedro_aguirre_cerda",
                "tipo_emergencia": "fuga_agua",
                "descripcion": "Fuga en la calle",
                "direccion": "Calle Principal 123",
                "nombre_usuario": "Juan Pérez",
                "telefono": "+56912345678"
            })
        ]
        
        mock_model = Mock()
        mock_model.generate_content.side_effect = [
            Mock(text=responses[0])
        ]
        mock_genai.GenerativeModel.return_value = mock_model
        
        # 1. Iniciar chat
        response = self.client.post(reverse('chat-init'), {}, format='json')
        self.assertEqual(response.status_code, 200)
        session_id = response.data['session_id']
        
        # 2. Enviar mensaje con toda la información
        response = self.client.post(
            reverse('chat-message'),
            {
                'session_id': session_id,
                'message': 'Tengo una fuga de agua en Calle Principal 123, sector Pedro Aguirre Cerda. Mi nombre es Juan Pérez y mi teléfono es +56912345678'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que la conversación progresa
        conversation = ChatConversation.objects.get(session_id=session_id)
        self.assertIsNotNone(conversation)


class RAGSystemTests(TestCase):
    """Tests para el sistema RAG (solo si está configurado)"""

    @patch('ModuloEmergencia.RAG.vector_store.chromadb')
    def test_vector_store_initialization(self, mock_chromadb):
        """Test: Vector store se puede inicializar"""
        from ModuloEmergencia.RAG.vector_store import VectorStoreManager
        
        mock_client = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        
        manager = VectorStoreManager()
        self.assertIsNotNone(manager)

    def test_document_processor_can_split_text(self):
        """Test: Document processor puede dividir texto"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        
        processor = DocumentProcessor()
        text = "Este es un texto de prueba. " * 100
        chunks = processor.process_text(text, metadata={"source": "test"})
        
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all('page_content' in chunk for chunk in chunks))
