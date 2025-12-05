"""
Script de verificación del sistema
Ejecutar con: python test_system.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_backend.settings')
django.setup()

from django.conf import settings
from ModuloEmergencia.RAG.vector_store import get_vector_store
from ModuloEmergencia.RAG.retriever import get_rag_retriever
from ModuloEmergencia.services.chatbot_service import get_chatbot_service
from ModuloEmergencia.models import Emergencia, ChatConversation, ChatMessage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_env():
    """Verifica configuración de environment"""
    logger.info("=== Verificando Configuración ===")
    
    checks = {
        "GEMINI_API_KEY": settings.GEMINI_API_KEY,
        "ChromaDB Path": settings.CHROMADB_PATH,
        "Debug Mode": settings.DEBUG,
        "Database": settings.DATABASES['default']['ENGINE']
    }
    
    all_ok = True
    for key, value in checks.items():
        if not value:
            logger.warning(f"❌ {key}: NO CONFIGURADO")
            all_ok = False
        else:
            logger.info(f"✅ {key}: {value}")
    
    return all_ok


def check_database():
    """Verifica conexión a base de datos"""
    logger.info("\n=== Verificando Base de Datos ===")
    
    try:
        # Contar registros
        emergencias_count = Emergencia.objects.count()
        conversaciones_count = ChatConversation.objects.count()
        mensajes_count = ChatMessage.objects.count()
        
        logger.info(f"✅ Emergencias: {emergencias_count}")
        logger.info(f"✅ Conversaciones: {conversaciones_count}")
        logger.info(f"✅ Mensajes: {mensajes_count}")
        return True
    except Exception as e:
        logger.error(f"❌ Error en base de datos: {e}")
        return False


def check_rag():
    """Verifica sistema RAG"""
    logger.info("\n=== Verificando Sistema RAG ===")
    
    try:
        # Vector store
        vector_store = get_vector_store()
        info = vector_store.get_collection_info()
        doc_count = info.get('count', 0)
        
        if doc_count == 0:
            logger.warning("❌ ChromaDB vacío - ejecutar ingest_documents.py")
            return False
        
        logger.info(f"✅ Documentos en ChromaDB: {doc_count}")
        
        # Retriever
        retriever = get_rag_retriever()
        results = retriever.retrieve("emergencia", top_k=2)
        
        if results:
            logger.info(f"✅ Recuperación funcionando: {len(results)} resultados")
            return True
        else:
            logger.warning("❌ No se pueden recuperar documentos")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en RAG: {e}")
        return False


def check_chatbot():
    """Verifica servicio de chatbot"""
    logger.info("\n=== Verificando Chatbot Service ===")
    
    try:
        chatbot = get_chatbot_service()
        logger.info("✅ ChatbotService inicializado")
        
        # Verificar Gemini
        if not settings.GEMINI_API_KEY:
            logger.warning("❌ GEMINI_API_KEY no configurada")
            return False
        
        logger.info("✅ Gemini API key configurada")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en ChatbotService: {e}")
        return False


def run_integration_test():
    """Prueba de integración básica"""
    logger.info("\n=== Prueba de Integración ===")
    
    try:
        chatbot = get_chatbot_service()
        
        # Crear conversación de prueba
        session_id = "test-session-123"
        
        # Limpiar si existe
        ChatConversation.objects.filter(session_id=session_id).delete()
        
        # Iniciar conversación
        conversation, initial_msg = chatbot.start_conversation(session_id)
        logger.info(f"✅ Conversación creada: {session_id}")
        logger.info(f"   Mensaje: {initial_msg[:50]}...")
        
        # Enviar mensaje de prueba
        response = chatbot.process_message(
            session_id,
            "Tengo una fuga de agua en El Molino"
        )
        
        logger.info(f"✅ Respuesta recibida")
        logger.info(f"   Estado: {response.get('estado')}")
        logger.info(f"   Mensaje: {response.get('message', '')[:100]}...")
        
        # Limpiar
        conversation.delete()
        logger.info("✅ Test completado y limpiado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en prueba de integración: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todas las verificaciones"""
    logger.info("🚀 Iniciando Verificación del Sistema\n")
    
    results = {
        "Configuración": check_env(),
        "Base de Datos": check_database(),
        "Sistema RAG": check_rag(),
        "Chatbot Service": check_chatbot(),
        "Prueba de Integración": run_integration_test()
    }
    
    logger.info("\n" + "="*60)
    logger.info("📊 RESUMEN DE VERIFICACIÓN")
    logger.info("="*60)
    
    for check, status in results.items():
        status_icon = "✅" if status else "❌"
        logger.info(f"{status_icon} {check}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 ¡Todos los checks pasaron! El sistema está listo.")
        logger.info("\n📝 Próximos pasos:")
        logger.info("   1. Iniciar servidor: python manage.py runserver")
        logger.info("   2. Probar API: POST http://localhost:8000/api/emergencias/chat/init/")
        logger.info("   3. Ver admin: http://localhost:8000/admin/")
    else:
        logger.error("\n⚠️  Algunos checks fallaron. Revisar logs arriba.")
        logger.info("\n🔧 Posibles soluciones:")
        if not results["Configuración"]:
            logger.info("   - Configurar GEMINI_API_KEY en .env")
        if not results["Sistema RAG"]:
            logger.info("   - Ejecutar: python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py")
        if not results["Base de Datos"]:
            logger.info("   - Ejecutar: python manage.py migrate")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
