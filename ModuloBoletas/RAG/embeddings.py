"""
Document Embeddings Manager
Procesa y genera embeddings para documentos sobre boletas
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import logging
from django.conf import settings

# Document loaders
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader
)

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Procesa documentos sobre boletas y los prepara para el sistema RAG
    """
    
    def __init__(self):
        """
        Inicializa el procesador de documentos
        """
        self.chunk_size = settings.RAG_CONFIG.get('chunk_size', 1000)
        self.chunk_overlap = settings.RAG_CONFIG.get('chunk_overlap', 200)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"DocumentProcessor inicializado (chunk_size={self.chunk_size})")
    
    def load_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Carga un documento según su extensión
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Lista de documentos procesados
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"Archivo no encontrado: {file_path}")
            return []
        
        try:
            # Seleccionar el loader apropiado
            if path.suffix == '.txt':
                loader = TextLoader(str(path), encoding='utf-8')
            elif path.suffix == '.pdf':
                loader = PyPDFLoader(str(path))
            elif path.suffix in ['.doc', '.docx']:
                loader = Docx2txtLoader(str(path))
            elif path.suffix == '.md':
                loader = UnstructuredMarkdownLoader(str(path))
            else:
                logger.warning(f"Tipo de archivo no soportado: {path.suffix}")
                return []
            
            # Cargar documentos
            documents = loader.load()
            logger.info(f"Documento cargado: {file_path} ({len(documents)} páginas/secciones)")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error al cargar documento {file_path}: {e}")
            return []
    
    def split_documents(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """
        Divide documentos en chunks más pequeños
        
        Args:
            documents: Lista de documentos de LangChain
            
        Returns:
            Lista de chunks procesados
        """
        try:
            # Dividir documentos
            chunks = self.text_splitter.split_documents(documents)
            
            # Preparar chunks con metadatos
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # Generar ID único basado en contenido
                chunk_id = self._generate_chunk_id(chunk.page_content, i)
                
                # Extraer metadatos
                metadata = chunk.metadata.copy() if hasattr(chunk, 'metadata') else {}
                metadata['chunk_index'] = i
                metadata['chunk_id'] = chunk_id
                
                processed_chunks.append({
                    'content': chunk.page_content,
                    'metadata': metadata,
                    'id': chunk_id
                })
            
            logger.info(f"Generados {len(processed_chunks)} chunks")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Error al dividir documentos: {e}")
            return []
    
    def _generate_chunk_id(self, content: str, index: int) -> str:
        """
        Genera un ID único para un chunk
        
        Args:
            content: Contenido del chunk
            index: Índice del chunk
            
        Returns:
            ID único
        """
        # Hash del contenido + índice
        hash_content = hashlib.md5(f"{content}{index}".encode()).hexdigest()
        return f"boleta_chunk_{hash_content[:16]}"
    
    def process_knowledge_base(self, knowledge_base_path: str) -> List[Dict[str, Any]]:
        """
        Procesa todos los documentos en el directorio de knowledge base
        
        Args:
            knowledge_base_path: Ruta al directorio con documentos
            
        Returns:
            Lista de todos los chunks procesados
        """
        kb_path = Path(knowledge_base_path)
        
        if not kb_path.exists():
            logger.error(f"Directorio de knowledge base no encontrado: {knowledge_base_path}")
            return []
        
        all_chunks = []
        supported_extensions = ['.txt', '.pdf', '.doc', '.docx', '.md']
        
        # Buscar todos los archivos soportados
        for ext in supported_extensions:
            for file_path in kb_path.rglob(f'*{ext}'):
                logger.info(f"Procesando: {file_path}")
                
                # Cargar documento
                documents = self.load_document(str(file_path))
                
                if documents:
                    # Dividir en chunks
                    chunks = self.split_documents(documents)
                    
                    # Agregar metadato del archivo fuente
                    for chunk in chunks:
                        chunk['metadata']['source_file'] = file_path.name
                        chunk['metadata']['source_path'] = str(file_path)
                    
                    all_chunks.extend(chunks)
        
        logger.info(f"Total de chunks procesados: {len(all_chunks)}")
        return all_chunks
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información del modelo de embeddings
        
        Returns:
            Dict con información del modelo
        """
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'embedding_model': 'ChromaDB default (all-MiniLM-L6-v2)',
            'status': 'active'
        }


# Singleton
_document_processor_instance = None


def get_document_processor() -> DocumentProcessor:
    """
    Obtiene la instancia singleton del DocumentProcessor
    
    Returns:
        DocumentProcessor: Instancia del procesador
    """
    global _document_processor_instance
    if _document_processor_instance is None:
        _document_processor_instance = DocumentProcessor()
    return _document_processor_instance
