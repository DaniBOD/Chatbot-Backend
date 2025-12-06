"""
Ingest Documents - Procesa y carga documentos en la base de datos vectorial
Script para inicializar la base de conocimientos de boletas
"""
import logging
from pathlib import Path
from typing import List, Dict, Any
from django.conf import settings

from .vector_store import get_vector_store
from .embeddings import get_document_processor

logger = logging.getLogger(__name__)


class DocumentIngester:
    """
    Gestiona la ingesta de documentos a la base de datos vectorial
    """
    
    def __init__(self):
        """
        Inicializa el ingestor de documentos
        """
        self.vector_store = get_vector_store()
        self.document_processor = get_document_processor()
        
        logger.info("DocumentIngester inicializado")
    
    def ingest_knowledge_base(self, force_reset: bool = False) -> Dict[str, Any]:
        """
        Ingesta todos los documentos del directorio knowledge_base
        
        Args:
            force_reset: Si True, reinicia la colección antes de ingestar
            
        Returns:
            Dict con resultados de la ingesta
        """
        # Ruta a knowledge_base
        kb_path = Path(__file__).parent / 'knowledge_base'
        
        if not kb_path.exists():
            logger.warning(f"Directorio knowledge_base no encontrado: {kb_path}")
            kb_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio knowledge_base creado: {kb_path}")
            return {
                'success': False,
                'message': 'Directorio knowledge_base creado. Agrega documentos y ejecuta nuevamente.',
                'documents_processed': 0
            }
        
        # Verificar si hay documentos
        supported_files = list(kb_path.rglob('*.txt')) + \
                         list(kb_path.rglob('*.pdf')) + \
                         list(kb_path.rglob('*.md')) + \
                         list(kb_path.rglob('*.docx'))
        
        if not supported_files:
            logger.warning("No se encontraron documentos en knowledge_base")
            return {
                'success': False,
                'message': 'No se encontraron documentos para procesar',
                'documents_processed': 0
            }
        
        # Reiniciar colección si se solicita
        if force_reset:
            logger.info("Reiniciando colección...")
            self.vector_store.reset_collection()
        
        try:
            # Procesar documentos
            logger.info(f"Procesando {len(supported_files)} archivos...")
            chunks = self.document_processor.process_knowledge_base(str(kb_path))
            
            if not chunks:
                return {
                    'success': False,
                    'message': 'No se generaron chunks de los documentos',
                    'documents_processed': 0
                }
            
            # Preparar datos para ChromaDB
            documents = [chunk['content'] for chunk in chunks]
            metadatas = [chunk['metadata'] for chunk in chunks]
            ids = [chunk['id'] for chunk in chunks]
            
            # Agregar a vector store
            success = self.vector_store.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Documentos ingestados exitosamente',
                    'files_processed': len(supported_files),
                    'chunks_generated': len(chunks),
                    'documents_added': len(documents)
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al agregar documentos al vector store',
                    'chunks_generated': len(chunks)
                }
                
        except Exception as e:
            logger.error(f"Error en ingesta: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'documents_processed': 0
            }
    
    def ingest_single_file(self, file_path: str) -> Dict[str, Any]:
        """
        Ingesta un archivo individual
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Dict con resultados
        """
        try:
            # Cargar documento
            documents = self.document_processor.load_document(file_path)
            
            if not documents:
                return {
                    'success': False,
                    'message': 'No se pudo cargar el documento'
                }
            
            # Dividir en chunks
            chunks = self.document_processor.split_documents(documents)
            
            if not chunks:
                return {
                    'success': False,
                    'message': 'No se generaron chunks'
                }
            
            # Preparar datos
            docs = [chunk['content'] for chunk in chunks]
            metas = [chunk['metadata'] for chunk in chunks]
            ids = [chunk['id'] for chunk in chunks]
            
            # Agregar a vector store
            success = self.vector_store.add_documents(
                documents=docs,
                metadatas=metas,
                ids=ids
            )
            
            return {
                'success': success,
                'message': 'Archivo ingestado' if success else 'Error al ingestar',
                'chunks_generated': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error ingestando archivo: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la ingesta
        
        Returns:
            Dict con estadísticas
        """
        return self.vector_store.get_collection_stats()


# Singleton
_document_ingester_instance = None


def get_document_ingester() -> DocumentIngester:
    """
    Obtiene la instancia singleton del DocumentIngester
    
    Returns:
        DocumentIngester: Instancia del ingestor
    """
    global _document_ingester_instance
    if _document_ingester_instance is None:
        _document_ingester_instance = DocumentIngester()
    return _document_ingester_instance


# Script de inicialización
def initialize_knowledge_base(force_reset: bool = False) -> Dict[str, Any]:
    """
    Función de utilidad para inicializar la base de conocimientos
    
    Args:
        force_reset: Si True, reinicia la colección
        
    Returns:
        Dict con resultados
    """
    ingester = get_document_ingester()
    return ingester.ingest_knowledge_base(force_reset=force_reset)
