"""
Vector Store Manager - ChromaDB Integration
Gestiona la base de datos vectorial para el sistema RAG
"""
import chromadb
from chromadb.config import Settings
from django.conf import settings
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Gestiona las operaciones de la base de datos vectorial ChromaDB
    """
    
    def __init__(self):
        """
        Inicializa la conexión con ChromaDB
        """
        self.chroma_path = settings.CHROMADB_PATH
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Colección para documentos de emergencias
        self.collection_name = "emergencias_knowledge_base"
        self.collection = self._get_or_create_collection()
        
        logger.info(f"VectorStoreManager inicializado con colección: {self.collection_name}")
    
    def _get_or_create_collection(self):
        """
        Obtiene o crea la colección en ChromaDB
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Colección existente cargada: {self.collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Base de conocimiento para emergencias de agua potable"}
            )
            logger.info(f"Nueva colección creada: {self.collection_name}")
        
        return collection
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """
        Agrega documentos a la base de datos vectorial
        
        Args:
            documents: Lista de textos a almacenar
            metadatas: Lista de metadatos asociados a cada documento
            ids: Lista de IDs únicos para cada documento
            
        Returns:
            bool: True si se agregaron correctamente
        """
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Agregados {len(documents)} documentos a la colección")
            return True
        except Exception as e:
            logger.error(f"Error al agregar documentos: {e}")
            return False
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Realiza una búsqueda semántica en la base de datos vectorial
        
        Args:
            query_text: Texto de la consulta
            n_results: Número de resultados a retornar
            where: Filtros de metadatos (opcional)
            
        Returns:
            Dict con los resultados de la búsqueda
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            logger.info(f"Búsqueda realizada: {n_results} resultados solicitados")
            return results
        except Exception as e:
            logger.error(f"Error en la búsqueda: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def get_all_documents(self) -> Dict[str, Any]:
        """
        Obtiene todos los documentos de la colección
        
        Returns:
            Dict con todos los documentos
        """
        try:
            count = self.collection.count()
            if count == 0:
                return {"documents": [], "metadatas": [], "ids": []}
            
            results = self.collection.get()
            logger.info(f"Obtenidos {count} documentos de la colección")
            return results
        except Exception as e:
            logger.error(f"Error al obtener documentos: {e}")
            return {"documents": [], "metadatas": [], "ids": []}
    
    def delete_collection(self) -> bool:
        """
        Elimina la colección completa (usar con precaución)
        
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.warning(f"Colección eliminada y recreada: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar colección: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre la colección
        
        Returns:
            Dict con información de la colección
        """
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            logger.error(f"Error al obtener info de colección: {e}")
            return {}


# Singleton para reutilizar la conexión
_vector_store_instance = None


def get_vector_store() -> VectorStoreManager:
    """
    Obtiene la instancia singleton del VectorStoreManager
    
    Returns:
        VectorStoreManager: Instancia del gestor de vectores
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreManager()
    return _vector_store_instance
