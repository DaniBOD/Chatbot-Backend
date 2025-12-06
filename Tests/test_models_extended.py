"""
Tests adicionales para modelos (extendidos).
Mejora cobertura de models.py de 90% a 95%+
"""

import unittest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from ModuloEmergencia.models import Emergencia, ChatConversation, ChatMessage
from datetime import timedelta
import uuid


class EmergenciaModelExtendedTests(TestCase):
    """Tests extendidos para el modelo Emergencia"""
    
    def test_emergencia_str_representation(self):
        """Test representación string del modelo"""
        emergencia = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Fuga en calle',
            direccion='Calle 123',
            nombre_usuario='Juan',
            telefono='+56911111111',
            nivel_prioridad='media'
        )
        
        str_repr = str(emergencia)
        self.assertIsInstance(str_repr, str)
        self.assertIn('anibana', str_repr.lower())
    
    def test_emergencia_all_sectors(self):
        """Test crear emergencia en todos los sectores"""
        sectores = [
            'anibana', 'pedro_aguirre_cerda', 'villa_san_jose',
            'el_molino', 'el_laurel', 'huara', 'punta_patache'
        ]
        
        for sector in sectores:
            emergencia = Emergencia.objects.create(
                sector=sector,
                tipo_emergencia='fuga_agua',
                descripcion='Test',
                direccion='Test',
                nombre_usuario='Test',
                telefono='+56911111111',
                nivel_prioridad='media'
            )
            self.assertEqual(emergencia.sector, sector)
    
    def test_emergencia_all_tipos(self):
        """Test crear emergencia con todos los tipos"""
        tipos = [
            'rotura_matriz', 'fuga_agua', 'caneria_rota',
            'corte_suministro', 'baja_presion', 'agua_contaminada',
            'otro'
        ]
        
        for tipo in tipos:
            emergencia = Emergencia.objects.create(
                sector='anibana',
                tipo_emergencia=tipo,
                descripcion='Test',
                direccion='Test',
                nombre_usuario='Test',
                telefono='+56911111111',
                nivel_prioridad='media'
            )
            self.assertEqual(emergencia.tipo_emergencia, tipo)
    
    def test_emergencia_all_prioridades(self):
        """Test crear emergencia con todas las prioridades"""
        prioridades = ['baja', 'media', 'alta', 'critica']
        
        for prioridad in prioridades:
            emergencia = Emergencia.objects.create(
                sector='anibana',
                tipo_emergencia='fuga_agua',
                descripcion='Test',
                direccion='Test',
                nombre_usuario='Test',
                telefono='+56911111111',
                nivel_prioridad=prioridad
            )
            self.assertEqual(emergencia.nivel_prioridad, prioridad)
    
    def test_emergencia_with_fotografia(self):
        """Test emergencia con fotografía"""
        emergencia = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Test',
            direccion='Test',
            nombre_usuario='Test',
            telefono='+56911111111',
            nivel_prioridad='media',
            fotografia='https://example.com/photo.jpg'
        )
        
        self.assertEqual(emergencia.fotografia, 'https://example.com/photo.jpg')
    
    def test_emergencia_without_fotografia(self):
        """Test emergencia sin fotografía (opcional)"""
        emergencia = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Test',
            direccion='Test',
            nombre_usuario='Test',
            telefono='+56911111111',
            nivel_prioridad='media'
        )
        
        self.assertIsNone(emergencia.fotografia)
    
    def test_emergencia_fecha_reporte_auto_set(self):
        """Test que fecha_reporte se establece automáticamente"""
        before = timezone.now()
        emergencia = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Test',
            direccion='Test',
            nombre_usuario='Test',
            telefono='+56911111111',
            nivel_prioridad='media'
        )
        after = timezone.now()
        
        self.assertIsNotNone(emergencia.fecha_reporte)
        self.assertTrue(before <= emergencia.fecha_reporte <= after)
    
    def test_emergencia_fecha_actualizacion_updates(self):
        """Test que fecha_actualizacion se actualiza automáticamente"""
        emergencia = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Test original',
            direccion='Test',
            nombre_usuario='Test',
            telefono='+56911111111',
            nivel_prioridad='media'
        )
        
        fecha_original = emergencia.fecha_actualizacion
        
        # Actualizar la emergencia
        emergencia.descripcion = 'Test actualizado'
        emergencia.save()
        
        emergencia.refresh_from_db()
        self.assertGreaterEqual(emergencia.fecha_actualizacion, fecha_original)
    
    def test_emergencia_descripcion_larga(self):
        """Test emergencia con descripción larga"""
        descripcion_larga = "Descripción muy larga. " * 100
        
        emergencia = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion=descripcion_larga,
            direccion='Test',
            nombre_usuario='Test',
            telefono='+56911111111',
            nivel_prioridad='media'
        )
        
        self.assertEqual(emergencia.descripcion, descripcion_larga)
    
    def test_emergencia_telefono_formats(self):
        """Test diferentes formatos de teléfono"""
        formatos = [
            '+56912345678',
            '56912345678',
            '+56 9 1234 5678',
        ]
        
        for telefono in formatos:
            emergencia = Emergencia.objects.create(
                sector='anibana',
                tipo_emergencia='fuga_agua',
                descripcion='Test',
                direccion='Test',
                nombre_usuario='Test',
                telefono=telefono,
                nivel_prioridad='media'
            )
            self.assertEqual(emergencia.telefono, telefono)


class ChatConversationModelExtendedTests(TestCase):
    """Tests extendidos para el modelo ChatConversation"""
    
    def test_conversation_str_representation(self):
        """Test representación string del modelo"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='iniciada',
            datos_recolectados={}
        )
        
        str_repr = str(conversation)
        self.assertIsInstance(str_repr, str)
    
    def test_conversation_all_estados(self):
        """Test conversación con todos los estados posibles"""
        estados = [
            'iniciada', 'recolectando_datos', 'calculando_prioridad',
            'solicitando_contacto', 'finalizada', 'cancelada'
        ]
        
        for estado in estados:
            conversation = ChatConversation.objects.create(
                session_id=uuid.uuid4(),
                estado=estado,
                datos_recolectados={}
            )
            self.assertEqual(conversation.estado, estado)
    
    def test_conversation_datos_recolectados_empty(self):
        """Test conversación con datos_recolectados vacío"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='iniciada',
            datos_recolectados={}
        )
        
        self.assertEqual(conversation.datos_recolectados, {})
    
    def test_conversation_datos_recolectados_full(self):
        """Test conversación con todos los datos recolectados"""
        datos = {
            'sector': 'anibana',
            'descripcion': 'Fuga de agua',
            'direccion': 'Calle 123',
            'nombre_usuario': 'Juan',
            'telefono': '+56911111111',
            'tipo_emergencia': 'fuga_agua',
            'fotografia': 'https://example.com/photo.jpg'
        }
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='finalizada',
            datos_recolectados=datos
        )
        
        self.assertEqual(conversation.datos_recolectados, datos)
    
    def test_conversation_with_emergencia_relation(self):
        """Test conversación asociada a una emergencia"""
        emergencia = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Test',
            direccion='Test',
            nombre_usuario='Test',
            telefono='+56911111111',
            nivel_prioridad='media'
        )
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='finalizada',
            datos_recolectados={},
            emergencia=emergencia
        )
        
        self.assertEqual(conversation.emergencia, emergencia)
    
    def test_conversation_without_emergencia(self):
        """Test conversación sin emergencia asociada"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='iniciada',
            datos_recolectados={}
        )
        
        self.assertIsNone(conversation.emergencia)
    
    def test_conversation_fecha_inicio_auto_set(self):
        """Test que fecha_inicio se establece automáticamente"""
        before = timezone.now()
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='iniciada',
            datos_recolectados={}
        )
        after = timezone.now()
        
        self.assertIsNotNone(conversation.fecha_inicio)
        self.assertTrue(before <= conversation.fecha_inicio <= after)
    
    def test_conversation_fecha_fin_initially_null(self):
        """Test que fecha_fin inicialmente es null"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='iniciada',
            datos_recolectados={}
        )
        
        self.assertIsNone(conversation.fecha_fin)
    
    def test_conversation_fecha_fin_can_be_set(self):
        """Test que fecha_fin puede establecerse"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='finalizada',
            datos_recolectados={},
            fecha_fin=timezone.now()
        )
        
        self.assertIsNotNone(conversation.fecha_fin)
    
    def test_conversation_session_id_unique(self):
        """Test que session_id es único"""
        session_id = uuid.uuid4()
        
        ChatConversation.objects.create(
            session_id=session_id,
            estado='iniciada',
            datos_recolectados={}
        )
        
        # Intentar crear otra con el mismo session_id debe fallar
        with self.assertRaises(Exception):
            ChatConversation.objects.create(
                session_id=session_id,
                estado='iniciada',
                datos_recolectados={}
            )


class ChatMessageModelExtendedTests(TestCase):
    """Tests extendidos para el modelo ChatMessage"""
    
    def setUp(self):
        """Crear conversación de prueba"""
        self.conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
    
    def test_message_str_representation(self):
        """Test representación string del modelo"""
        message = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido='Hola'
        )
        
        str_repr = str(message)
        self.assertIsInstance(str_repr, str)
        self.assertIn('usuario', str_repr.lower())
    
    def test_message_rol_usuario(self):
        """Test mensaje con rol usuario"""
        message = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido='Mensaje del usuario'
        )
        
        self.assertEqual(message.rol, 'usuario')
    
    def test_message_rol_asistente(self):
        """Test mensaje con rol asistente"""
        message = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='asistente',
            contenido='Mensaje del asistente'
        )
        
        self.assertEqual(message.rol, 'asistente')
    
    def test_message_timestamp_auto_set(self):
        """Test que timestamp se establece automáticamente"""
        before = timezone.now()
        message = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido='Test'
        )
        after = timezone.now()
        
        self.assertIsNotNone(message.timestamp)
        self.assertTrue(before <= message.timestamp <= after)
    
    def test_message_contenido_largo(self):
        """Test mensaje con contenido largo"""
        contenido_largo = "Palabra " * 1000
        
        message = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido=contenido_largo
        )
        
        self.assertEqual(message.contenido, contenido_largo)
    
    def test_message_contenido_con_caracteres_especiales(self):
        """Test mensaje con caracteres especiales"""
        contenido = "Hola! ¿Cómo estás? Tengo $100 y @usuario #test"
        
        message = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido=contenido
        )
        
        self.assertEqual(message.contenido, contenido)
    
    def test_message_contenido_multilinea(self):
        """Test mensaje con contenido multilínea"""
        contenido = """
        Línea 1
        Línea 2
        Línea 3
        """
        
        message = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido=contenido
        )
        
        self.assertEqual(message.contenido, contenido)
    
    def test_message_ordering(self):
        """Test ordenamiento de mensajes por timestamp"""
        # Crear varios mensajes
        message1 = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido='Primero'
        )
        message2 = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='asistente',
            contenido='Segundo'
        )
        message3 = ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido='Tercero'
        )
        
        # Obtener mensajes ordenados
        messages = ChatMessage.objects.filter(
            conversation=self.conversation
        ).order_by('timestamp')
        
        self.assertEqual(messages[0].contenido, 'Primero')
        self.assertEqual(messages[1].contenido, 'Segundo')
        self.assertEqual(messages[2].contenido, 'Tercero')
    
    def test_message_conversation_cascade_delete(self):
        """Test que los mensajes se eliminan al eliminar la conversación"""
        ChatMessage.objects.create(
            conversation=self.conversation,
            rol='usuario',
            contenido='Mensaje de prueba'
        )
        
        # Eliminar la conversación
        conversation_id = self.conversation.id
        self.conversation.delete()
        
        # Verificar que los mensajes también se eliminaron
        messages = ChatMessage.objects.filter(conversation__id=conversation_id)
        self.assertEqual(messages.count(), 0)


class ModelRelationshipsTests(TestCase):
    """Tests de relaciones entre modelos"""
    
    def test_emergencia_has_conversation(self):
        """Test que una emergencia puede tener conversación asociada"""
        emergencia = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Test',
            direccion='Test',
            nombre_usuario='Test',
            telefono='+56911111111',
            nivel_prioridad='media'
        )
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='finalizada',
            datos_recolectados={},
            emergencia=emergencia
        )
        
        # Verificar relación inversa
        conversations = ChatConversation.objects.filter(emergencia=emergencia)
        self.assertEqual(conversations.count(), 1)
        self.assertEqual(conversations.first(), conversation)
    
    def test_conversation_has_multiple_messages(self):
        """Test que una conversación puede tener múltiples mensajes"""
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='recolectando_datos',
            datos_recolectados={}
        )
        
        # Crear varios mensajes
        for i in range(10):
            ChatMessage.objects.create(
                conversation=conversation,
                rol='usuario' if i % 2 == 0 else 'asistente',
                contenido=f'Mensaje {i}'
            )
        
        # Verificar que todos los mensajes están asociados
        messages = ChatMessage.objects.filter(conversation=conversation)
        self.assertEqual(messages.count(), 10)
    
    def test_delete_emergencia_nullifies_conversation(self):
        """Test que eliminar emergencia pone null en conversación"""
        emergencia = Emergencia.objects.create(
            sector='anibana',
            tipo_emergencia='fuga_agua',
            descripcion='Test',
            direccion='Test',
            nombre_usuario='Test',
            telefono='+56911111111',
            nivel_prioridad='media'
        )
        
        conversation = ChatConversation.objects.create(
            session_id=uuid.uuid4(),
            estado='finalizada',
            datos_recolectados={},
            emergencia=emergencia
        )
        
        # Eliminar emergencia
        emergencia.delete()
        
        # Verificar que la conversación sigue existiendo pero sin emergencia
        conversation.refresh_from_db()
        self.assertIsNone(conversation.emergencia)


class QuerySetTests(TestCase):
    """Tests de QuerySets y filtros"""
    
    def setUp(self):
        """Crear datos de prueba"""
        for i in range(5):
            Emergencia.objects.create(
                sector='anibana',
                tipo_emergencia='fuga_agua',
                descripcion=f'Emergencia {i}',
                direccion=f'Dirección {i}',
                nombre_usuario=f'Usuario {i}',
                telefono=f'+5691111111{i}',
                nivel_prioridad='media'
            )
    
    def test_filter_emergencias_by_sector(self):
        """Test filtrar emergencias por sector"""
        emergencias = Emergencia.objects.filter(sector='anibana')
        self.assertEqual(emergencias.count(), 5)
    
    def test_filter_emergencias_by_prioridad(self):
        """Test filtrar emergencias por prioridad"""
        emergencias = Emergencia.objects.filter(nivel_prioridad='media')
        self.assertEqual(emergencias.count(), 5)
    
    def test_order_emergencias_by_fecha(self):
        """Test ordenar emergencias por fecha"""
        emergencias = Emergencia.objects.all().order_by('-fecha_reporte')
        
        # Verificar que están en orden descendente
        for i in range(len(emergencias) - 1):
            self.assertGreaterEqual(
                emergencias[i].fecha_reporte,
                emergencias[i + 1].fecha_reporte
            )


if __name__ == '__main__':
    unittest.main()
