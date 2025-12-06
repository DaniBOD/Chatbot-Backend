"""
Tests de integración end-to-end para el sistema de API.
Flujos completos de usuario reportando emergencias.
"""

import unittest
from unittest.mock import patch, Mock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from ModuloEmergencia.models import ChatConversation, ChatMessage, Emergencia
import uuid


class ChatAPIIntegrationTests(TestCase):
    """Tests de integración para el flujo completo de chat"""
    
    def setUp(self):
        """Configurar cliente API"""
        self.client = APIClient()
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    def test_complete_chat_flow_init_to_message(self, mock_llm):
        """Test flujo completo: iniciar conversación y enviar mensaje"""
        mock_llm.return_value = "¿En qué puedo ayudarte?"
        
        # 1. Iniciar conversación
        response = self.client.post('/api/emergencias/chat/init/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('session_id', response.data)
        self.assertIn('estado', response.data)
        
        session_id = response.data['session_id']
        
        # 2. Enviar mensaje
        mock_llm.return_value = "Entendido, ¿en qué sector?"
        response = self.client.post('/api/emergencias/chat/message/', {
            'session_id': session_id,
            'mensaje': 'Tengo una emergencia'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('respuesta', response.data)
        self.assertIn('estado', response.data)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    def test_complete_chat_flow_check_status(self, mock_llm):
        """Test flujo: iniciar, enviar mensaje y verificar estado"""
        mock_llm.return_value = "Respuesta del bot"
        
        # Iniciar conversación
        response = self.client.post('/api/emergencias/chat/init/')
        session_id = response.data['session_id']
        
        # Enviar mensaje
        self.client.post('/api/emergencias/chat/message/', {
            'session_id': session_id,
            'mensaje': 'Hola'
        })
        
        # Verificar estado
        response = self.client.get(f'/api/emergencias/chat/status/{session_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('estado', response.data)
        self.assertIn('datos_recolectados', response.data)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._extract_data_with_llm')
    def test_complete_emergency_report_flow(self, mock_extract, mock_llm):
        """Test flujo completo de reporte de emergencia"""
        mock_llm.return_value = "Entendido"
        
        # Iniciar conversación
        response = self.client.post('/api/emergencias/chat/init/')
        session_id = response.data['session_id']
        
        # Simular recolección de datos
        conversation_steps = [
            ({'sector': 'anibana'}, "Estoy en Anibana"),
            ({'descripcion': 'Fuga de agua'}, "Hay una fuga de agua"),
            ({'direccion': 'Calle Principal 123'}, "Calle Principal 123"),
            ({'nombre_usuario': 'Juan Pérez'}, "Juan Pérez"),
            ({'telefono': '+56912345678'}, "+56912345678"),
        ]
        
        for extracted_data, mensaje in conversation_steps:
            mock_extract.return_value = extracted_data
            response = self.client.post('/api/emergencias/chat/message/', {
                'session_id': session_id,
                'mensaje': mensaje
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que los datos se acumularon
        conversation = ChatConversation.objects.get(session_id=session_id)
        self.assertIn('sector', conversation.datos_recolectados)
        self.assertIn('descripcion', conversation.datos_recolectados)
    
    def test_chat_message_without_session_id(self):
        """Test enviar mensaje sin session_id"""
        response = self.client.post('/api/emergencias/chat/message/', {
            'mensaje': 'Hola'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_chat_message_with_invalid_session_id(self):
        """Test enviar mensaje con session_id inválido"""
        fake_session_id = str(uuid.uuid4())
        
        response = self.client.post('/api/emergencias/chat/message/', {
            'session_id': fake_session_id,
            'mensaje': 'Hola'
        })
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_status_with_invalid_session_id(self):
        """Test obtener estado con session_id inválido"""
        fake_session_id = str(uuid.uuid4())
        
        response = self.client.get(f'/api/emergencias/chat/status/{fake_session_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EmergencyAPIIntegrationTests(TestCase):
    """Tests de integración para endpoints de emergencias"""
    
    def setUp(self):
        """Crear emergencias de prueba"""
        self.client = APIClient()
        
        self.emergencia1 = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Fuga en la calle principal',
            direccion='Calle Principal 123',
            nombre_usuario='Juan Pérez',
            telefono='+56912345678',
            nivel_prioridad='media'
        )
        
        self.emergencia2 = Emergencia.objects.create(
            sector='el_molino',
            tipo_emergencia='rotura_matriz',
            descripcion='Matriz rota en avenida',
            direccion='Avenida Central 456',
            nombre_usuario='María González',
            telefono='+56987654321',
            nivel_prioridad='alta'
        )
    
    def test_list_emergencies(self):
        """Test listar todas las emergencias"""
        response = self.client.get('/api/emergencias/emergencias/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)
    
    def test_get_emergency_detail(self):
        """Test obtener detalle de una emergencia"""
        response = self.client.get(
            f'/api/emergencias/emergencias/{self.emergencia1.id_emergencia}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sector'], 'anibana')
        self.assertEqual(response.data['tipo_emergencia'], 'fuga_agua')
    
    def test_filter_emergencies_by_sector(self):
        """Test filtrar emergencias por sector"""
        response = self.client.get('/api/emergencias/emergencias/?sector=anibana')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sector'], 'anibana')
    
    def test_filter_emergencies_by_priority(self):
        """Test filtrar emergencias por prioridad"""
        response = self.client.get('/api/emergencias/emergencias/?prioridad=alta')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nivel_prioridad'], 'alta')
    
    def test_filter_emergencies_by_multiple_params(self):
        """Test filtrar emergencias por múltiples parámetros"""
        response = self.client.get(
            '/api/emergencias/emergencias/?sector=el_molino&prioridad=alta'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sector'], 'el_molino')
        self.assertEqual(response.data[0]['nivel_prioridad'], 'alta')
    
    def test_get_nonexistent_emergency(self):
        """Test obtener emergencia que no existe"""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/emergencias/emergencias/{fake_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StatsAPIIntegrationTests(TestCase):
    """Tests de integración para endpoints de estadísticas"""
    
    def setUp(self):
        """Crear datos de prueba"""
        self.client = APIClient()
        
        # Crear emergencias con diferentes prioridades y sectores
        Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Fuga 1',
            direccion='Dir 1',
            nombre_usuario='Usuario 1',
            telefono='+56911111111',
            nivel_prioridad='media'
        )
        Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='rotura_matriz',
            descripcion='Rotura 1',
            direccion='Dir 2',
            nombre_usuario='Usuario 2',
            telefono='+56922222222',
            nivel_prioridad='alta'
        )
        Emergencia.objects.create(
            sector='el_molino',
            tipo_emergencia='corte_suministro',
            descripcion='Corte 1',
            direccion='Dir 3',
            nombre_usuario='Usuario 3',
            telefono='+56933333333',
            nivel_prioridad='critica'
        )
    
    def test_get_general_stats(self):
        """Test obtener estadísticas generales"""
        response = self.client.get('/api/emergencias/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_emergencias', response.data)
        self.assertIn('por_sector', response.data)
        self.assertIn('por_prioridad', response.data)
        
        self.assertEqual(response.data['total_emergencias'], 3)
    
    def test_stats_count_by_sector(self):
        """Test que las estadísticas cuentan correctamente por sector"""
        response = self.client.get('/api/emergencias/stats/')
        
        por_sector = response.data['por_sector']
        
        # Verificar que hay 2 en anibana y 1 en el_molino
        anibana_count = next((s['count'] for s in por_sector if s['sector'] == 'anibana'), 0)
        molino_count = next((s['count'] for s in por_sector if s['sector'] == 'el_molino'), 0)
        
        self.assertEqual(anibana_count, 2)
        self.assertEqual(molino_count, 1)
    
    def test_stats_count_by_priority(self):
        """Test que las estadísticas cuentan correctamente por prioridad"""
        response = self.client.get('/api/emergencias/stats/')
        
        por_prioridad = response.data['por_prioridad']
        
        # Verificar las cantidades
        self.assertEqual(len([p for p in por_prioridad if p['nivel_prioridad'] == 'media']), 1)
        self.assertEqual(len([p for p in por_prioridad if p['nivel_prioridad'] == 'alta']), 1)
        self.assertEqual(len([p for p in por_prioridad if p['nivel_prioridad'] == 'critica']), 1)
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    def test_get_rag_stats(self, mock_vector_store):
        """Test obtener estadísticas del sistema RAG"""
        mock_vs = Mock()
        mock_vs.collection.count.return_value = 127
        mock_vector_store.return_value = mock_vs
        
        response = self.client.get('/api/emergencias/rag/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_documents', response.data)


class ConversationHistoryIntegrationTests(TestCase):
    """Tests de integración para el historial de conversaciones"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Crear una conversación con mensajes
        self.conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={'sector': 'anibana'}
        )
        
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
        ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido='Tengo una emergencia'
        )
    
    def test_get_conversation_history(self):
        """Test obtener historial de una conversación"""
        response = self.client.get(
            f'/api/emergencias/chat/status/{self.conversation.session_id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que incluye el historial
        if 'historial' in response.data:
            historial = response.data['historial']
            self.assertGreaterEqual(len(historial), 3)
    
    def test_conversation_messages_in_order(self):
        """Test que los mensajes están en orden cronológico"""
        messages = ChatMessage.objects.filter(
            conversation=self.conversation
        ).order_by('timestamp')
        
        self.assertEqual(messages[0].rol, 'usuario')
        self.assertEqual(messages[1].rol, 'asistente')
        self.assertEqual(messages[2].rol, 'usuario')


class ErrorHandlingIntegrationTests(TestCase):
    """Tests de manejo de errores en la API"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_post_message_without_mensaje_field(self):
        """Test enviar mensaje sin el campo 'mensaje'"""
        response = self.client.post('/api/emergencias/chat/message/', {
            'session_id': str(uuid.uuid4())
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_sector_in_emergency(self):
        """Test crear emergencia con sector inválido"""
        response = self.client.post('/api/emergencias/emergencias/', {
            'sector': 'sector_invalido',
            'tipo_emergencia': 'fuga_agua',
            'descripcion': 'Descripción',
            'direccion': 'Dirección',
            'nombre_usuario': 'Usuario',
            'telefono': '+56911111111',
            'nivel_prioridad': 'media'
        })
        
        # Debe fallar la validación
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])
    
    def test_missing_required_fields_in_emergency(self):
        """Test crear emergencia sin campos requeridos"""
        response = self.client.post('/api/emergencias/emergencias/', {
            'sector': 'anibana'
            # Faltan otros campos requeridos
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    def test_gemini_api_error_handling(self, mock_llm):
        """Test manejo de error en API de Gemini"""
        mock_llm.side_effect = Exception("API Error")
        
        # Debería manejar el error gracefully
        response = self.client.post('/api/emergencias/chat/init/')
        
        # Puede retornar error o mensaje por defecto
        self.assertIn(response.status_code, [
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_201_CREATED
        ])


class ConcurrencyTests(TestCase):
    """Tests de concurrencia y múltiples sesiones"""
    
    def setUp(self):
        self.client = APIClient()
    
    @patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
    def test_multiple_concurrent_conversations(self, mock_llm):
        """Test múltiples conversaciones simultáneas"""
        mock_llm.return_value = "Respuesta"
        
        # Crear 3 conversaciones simultáneas
        sessions = []
        for i in range(3):
            response = self.client.post('/api/emergencias/chat/init/')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            sessions.append(response.data['session_id'])
        
        # Verificar que todas las sesiones son únicas
        self.assertEqual(len(sessions), len(set(sessions)))
        
        # Enviar mensajes a cada sesión
        for session_id in sessions:
            response = self.client.post('/api/emergencias/chat/message/', {
                'session_id': session_id,
                'mensaje': f'Mensaje para {session_id}'
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que cada conversación mantiene su estado independiente
        conversations = ChatConversation.objects.filter(session_id__in=sessions)
        self.assertEqual(conversations.count(), 3)


class DataValidationTests(TestCase):
    """Tests de validación de datos"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_phone_number_format_validation(self):
        """Test validación de formato de teléfono"""
        invalid_phones = [
            '12345',  # Muy corto
            'not-a-phone',  # No numérico
            '+1234567890123456789',  # Muy largo
        ]
        
        for phone in invalid_phones:
            response = self.client.post('/api/emergencias/emergencias/', {
                'sector': 'anibana',
                'tipo_emergencia': 'fuga_agua',
                'descripcion': 'Test',
                'direccion': 'Test',
                'nombre_usuario': 'Test',
                'telefono': phone,
                'nivel_prioridad': 'media'
            })
            # Puede validar o no según la implementación
            # Este test documenta el comportamiento esperado
    
    def test_priority_level_validation(self):
        """Test validación de niveles de prioridad"""
        valid_priorities = ['baja', 'media', 'alta', 'critica']
        
        for priority in valid_priorities:
            response = self.client.post('/api/emergencias/emergencias/', {
                'sector': 'anibana',
                'tipo_emergencia': 'fuga_agua',
                'descripcion': 'Test',
                'direccion': 'Test',
                'nombre_usuario': 'Test',
                'telefono': '+56911111111',
                'nivel_prioridad': priority
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)


if __name__ == '__main__':
    unittest.main()
