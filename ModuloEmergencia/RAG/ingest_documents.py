"""
Script para ingestar documentos a la base de conocimiento RAG
Ejecutar con: python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_backend.settings')
django.setup()

from ModuloEmergencia.RAG.embeddings import get_document_processor
from ModuloEmergencia.RAG.vector_store import get_vector_store
from django.conf import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_knowledge_base():
    """
    Ingesta todos los documentos de la carpeta knowledge_base
    """
    logger.info("=== Iniciando ingesta de documentos ===")
    
    # Obtener instancias
    processor = get_document_processor()
    vector_store = get_vector_store()
    
    # Ruta a knowledge_base
    kb_path = settings.BASE_DIR / 'ModuloEmergencia' / 'RAG' / 'knowledge_base'
    
    if not kb_path.exists():
        logger.error(f"Directorio no encontrado: {kb_path}")
        return
    
    logger.info(f"Procesando documentos de: {kb_path}")
    
    # Procesar directorio completo
    chunks = processor.process_directory(
        directory_path=str(kb_path),
        file_pattern="*.md"
    )
    
    if not chunks:
        logger.warning("No se procesaron documentos")
        return
    
    logger.info(f"Total de chunks procesados: {len(chunks)}")
    
    # Preparar datos para ChromaDB
    documents = []
    metadatas = []
    ids = []
    
    for chunk in chunks:
        documents.append(chunk['text'])
        metadatas.append(chunk['metadata'])
        ids.append(chunk['metadata']['chunk_id'])
    
    # Agregar a vector store
    logger.info("Agregando documentos a ChromaDB...")
    success = vector_store.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    if success:
        logger.info("✅ Documentos ingresados exitosamente")
        
        # Mostrar estadísticas
        info = vector_store.get_collection_info()
        logger.info(f"📊 Total de documentos en colección: {info.get('count', 0)}")
    else:
        logger.error("❌ Error al ingestar documentos")


def test_retrieval():
    """
    Prueba la recuperación de documentos
    """
    logger.info("\n=== Probando recuperación de documentos ===")
    
    from ModuloEmergencia.RAG.retriever import get_rag_retriever
    
    retriever = get_rag_retriever()
    
    # Pruebas de consulta
    test_queries = [
        "¿Qué hacer en caso de rotura de matriz?",
        "¿Cuáles son los sectores atendidos?",
        "¿Cuál es el teléfono de emergencias?",
        "¿Cómo se calcula la prioridad de una emergencia?"
    ]
    
    for query in test_queries:
        logger.info(f"\n🔍 Consulta: {query}")
        results = retriever.retrieve(query, top_k=2)
        
        if results:
            logger.info(f"✅ Encontrados {len(results)} resultados")
            for i, result in enumerate(results, 1):
                logger.info(f"  {i}. Relevancia: {result['relevance_score']:.2f}")
                logger.info(f"     Contenido (primeros 100 chars): {result['content'][:100]}...")
        else:
            logger.warning("❌ No se encontraron resultados")


if __name__ == "__main__":
    try:
        ingest_knowledge_base()
        test_retrieval()
        logger.info("\n✅ Proceso completado exitosamente")
    except Exception as e:
        logger.error(f"\n❌ Error en el proceso: {e}")
        import traceback
        traceback.print_exc()
