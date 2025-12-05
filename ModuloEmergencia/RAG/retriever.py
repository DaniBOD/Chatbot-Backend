"""
RAG Retriever - Sistema de recuperación de información
Combina búsqueda vectorial con contexto para el chatbot
"""
from typing import List, Dict, Any, Optional
import logging
from django.conf import settings

from .vector_store import get_vector_store
from .embeddings import get_document_processor

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Sistema de recuperación de información augmentada por generación (RAG)
    """
    
    def __init__(self):
        """
        Inicializa el retriever RAG
        """
        self.vector_store = get_vector_store()
        self.document_processor = get_document_processor()
        self.top_k = settings.RAG_CONFIG.get('top_k_results', 5)
        
        logger.info("RAGRetriever inicializado")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera documentos relevantes para una consulta
        
        Args:
            query: Consulta del usuario
            top_k: Número de resultados a retornar (usa default si None)
            filters: Filtros de metadatos opcionales
            
        Returns:
            Lista de documentos relevantes con su información
        """
        k = top_k if top_k is not None else self.top_k
        
        try:
            # Realizar búsqueda vectorial
            results = self.vector_store.query(
                query_text=query,
                n_results=k,
                where=filters
            )
            
            # Formatear resultados
            formatted_results = self._format_results(results)
            
            logger.info(f"Recuperados {len(formatted_results)} documentos para: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error en recuperación: {e}")
            return []
    
    def retrieve_with_context(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recupera documentos y construye contexto enriquecido
        
        Args:
            query: Consulta actual del usuario
            conversation_history: Historial de conversación
            top_k: Número de resultados a retornar
            
        Returns:
            Dict con contexto completo para el LLM
        """
        # Recuperar documentos relevantes
        documents = self.retrieve(query, top_k)
        
        # Construir contexto
        context = self._build_context(
            query=query,
            documents=documents,
            conversation_history=conversation_history
        )
        
        return context
    
    def _format_results(self, raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formatea los resultados de ChromaDB
        
        Args:
            raw_results: Resultados crudos de ChromaDB
            
        Returns:
            Lista de documentos formateados
        """
        formatted = []
        
        try:
            documents = raw_results.get('documents', [[]])[0]
            metadatas = raw_results.get('metadatas', [[]])[0]
            distances = raw_results.get('distances', [[]])[0]
            ids = raw_results.get('ids', [[]])[0]
            
            for i, doc in enumerate(documents):
                formatted.append({
                    'id': ids[i] if i < len(ids) else None,
                    'content': doc,
                    'metadata': metadatas[i] if i < len(metadatas) else {},
                    'relevance_score': 1 - distances[i] if i < len(distances) else 0,
                    'distance': distances[i] if i < len(distances) else 1.0
                })
            
        except Exception as e:
            logger.error(f"Error al formatear resultados: {e}")
        
        return formatted
    
    def _build_context(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Construye el contexto completo para el LLM
        
        Args:
            query: Consulta actual
            documents: Documentos recuperados
            conversation_history: Historial de conversación
            
        Returns:
            Dict con contexto estructurado
        """
        # Preparar contexto de documentos
        doc_context = []
        for i, doc in enumerate(documents, 1):
            doc_context.append({
                'number': i,
                'content': doc['content'],
                'source': doc['metadata'].get('source_file', 'Unknown'),
                'relevance': doc['relevance_score']
            })
        
        # Preparar historial de conversación
        history_context = []
        if conversation_history:
            for msg in conversation_history[-5:]:  # Últimos 5 mensajes
                history_context.append({
                    'role': msg.get('role', 'unknown'),
                    'content': msg.get('content', '')
                })
        
        return {
            'query': query,
            'retrieved_documents': doc_context,
            'conversation_history': history_context,
            'num_documents': len(doc_context),
            'has_history': len(history_context) > 0
        }
    
    def get_relevant_context_text(
        self,
        query: str,
        max_length: int = 3000
    ) -> str:
        """
        Obtiene el texto de contexto relevante formateado para el prompt
        
        Args:
            query: Consulta del usuario
            max_length: Longitud máxima del contexto en caracteres
            
        Returns:
            Texto de contexto formateado
        """
        documents = self.retrieve(query)
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(documents, 1):
            content = doc['content']
            
            # Verificar si agregarlo excede el límite
            if current_length + len(content) > max_length:
                break
            
            context_parts.append(f"[Documento {i}]\n{content}\n")
            current_length += len(content)
        
        if not context_parts:
            return "No se encontró información relevante en la base de conocimiento."
        
        context_text = "\n".join(context_parts)
        return f"=== CONTEXTO DE LA BASE DE CONOCIMIENTO ===\n\n{context_text}\n=== FIN DEL CONTEXTO ==="
    
    def search_by_category(self, category: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Busca documentos por categoría específica
        
        Args:
            category: Categoría a buscar (ej: 'protocolos', 'contactos')
            top_k: Número de resultados
            
        Returns:
            Lista de documentos de la categoría
        """
        try:
            # Buscar con filtro de categoría
            results = self.vector_store.query(
                query_text=f"información sobre {category}",
                n_results=top_k,
                where={"category": category}
            )
            
            return self._format_results(results)
            
        except Exception as e:
            logger.error(f"Error en búsqueda por categoría: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la colección
        
        Returns:
            Dict con estadísticas
        """
        return self.vector_store.get_collection_info()


# Singleton
_rag_retriever_instance = None


def get_rag_retriever() -> RAGRetriever:
    """
    Obtiene la instancia singleton del RAGRetriever
    
    Returns:
        RAGRetriever: Instancia del retriever
    """
    global _rag_retriever_instance
    if _rag_retriever_instance is None:
        _rag_retriever_instance = RAGRetriever()
    return _rag_retriever_instance
