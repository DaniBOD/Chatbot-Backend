"""
Document Embeddings Manager
Procesa y genera embeddings para documentos
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
    Procesa documentos y los prepara para el sistema RAG
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
                processed_chunk = {
                    'text': chunk.page_content,
                    'metadata': {
                        **chunk.metadata,
                        'chunk_index': i,
                        'chunk_id': self._generate_chunk_id(chunk.page_content, i)
                    }
                }
                processed_chunks.append(processed_chunk)
            
            logger.info(f"Documentos divididos en {len(processed_chunks)} chunks")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Error al dividir documentos: {e}")
            return []
    
    def process_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Procesa texto plano directamente
        
        Args:
            text: Texto a procesar
            metadata: Metadatos opcionales
            
        Returns:
            Lista de chunks procesados
        """
        try:
            # Dividir texto
            chunks = self.text_splitter.split_text(text)
            
            # Preparar chunks
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata['chunk_index'] = i
                chunk_metadata['chunk_id'] = self._generate_chunk_id(chunk, i)
                
                processed_chunks.append({
                    'text': chunk,
                    'metadata': chunk_metadata
                })
            
            logger.info(f"Texto procesado en {len(processed_chunks)} chunks")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Error al procesar texto: {e}")
            return []
    
    def process_directory(
        self,
        directory_path: str,
        file_pattern: str = "*"
    ) -> List[Dict[str, Any]]:
        """
        Procesa todos los archivos en un directorio
        
        Args:
            directory_path: Ruta al directorio
            file_pattern: Patrón de archivos a procesar (ej: "*.txt")
            
        Returns:
            Lista de todos los chunks procesados
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"Directorio no encontrado: {directory_path}")
            return []
        
        all_chunks = []
        
        # Buscar archivos
        for file_path in directory.rglob(file_pattern):
            if file_path.is_file():
                # Cargar documento
                documents = self.load_document(str(file_path))
                
                if documents:
                    # Dividir en chunks
                    chunks = self.split_documents(documents)
                    
                    # Agregar metadato del archivo fuente
                    for chunk in chunks:
                        chunk['metadata']['source_file'] = str(file_path)
                    
                    all_chunks.extend(chunks)
        
        logger.info(f"Directorio procesado: {len(all_chunks)} chunks totales")
        return all_chunks
    
    def _generate_chunk_id(self, text: str, index: int) -> str:
        """
        Genera un ID único para un chunk
        
        Args:
            text: Texto del chunk
            index: Índice del chunk
            
        Returns:
            ID único del chunk
        """
        # Crear hash del contenido + índice
        content = f"{text}_{index}"
        return hashlib.md5(content.encode()).hexdigest()


class EmbeddingsManager:
    """
    Gestiona la generación de embeddings
    Nota: ChromaDB genera embeddings automáticamente usando sentence-transformers
    """
    
    def __init__(self):
        """
        Inicializa el gestor de embeddings
        """
        self.model_name = settings.RAG_CONFIG.get(
            'embedding_model',
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        )
        logger.info(f"EmbeddingsManager inicializado con modelo: {self.model_name}")
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Obtiene información sobre el modelo de embeddings
        
        Returns:
            Dict con información del modelo
        """
        return {
            "model_name": self.model_name,
            "provider": "ChromaDB (sentence-transformers)",
            "language_support": "Multilingual (incluye español)"
        }


# Singletons
_document_processor_instance = None
_embeddings_manager_instance = None


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


def get_embeddings_manager() -> EmbeddingsManager:
    """
    Obtiene la instancia singleton del EmbeddingsManager
    
    Returns:
        EmbeddingsManager: Instancia del gestor
    """
    global _embeddings_manager_instance
    if _embeddings_manager_instance is None:
        _embeddings_manager_instance = EmbeddingsManager()
    return _embeddings_manager_instance
