"""
RAG Retriever - Sistema de recuperación de información
Combina búsqueda vectorial con contexto para el chatbot de boletas
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
    para consultas sobre boletas de agua
    """
    
    def __init__(self):
        """
        Inicializa el retriever RAG
        """
        self.vector_store = get_vector_store()
        self.document_processor = get_document_processor()
        self.top_k = settings.RAG_CONFIG.get('top_k_results', 5)
        
        logger.info("RAGRetriever (Boletas) inicializado")
    
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
    
    def get_relevant_context_text(
        self,
        query: str,
        max_length: int = 2000,
        top_k: Optional[int] = None
    ) -> str:
        """
        Obtiene el contexto relevante como texto plano
        
        Args:
            query: Consulta del usuario
            max_length: Longitud máxima del contexto
            top_k: Número de resultados a considerar
            
        Returns:
            Contexto como texto plano
        """
        documents = self.retrieve(query, top_k)

        if not documents:
            return "No se encontró información relevante en la base de conocimientos."

        # Construir texto de contexto con fragmentos acotados y referencia a la fuente
        context_parts = ["INFORMACIÓN RELEVANTE (fragmentos y fuentes):"]
        current_length = len(context_parts[0])

        # Limitar la longitud por documento para evitar prompts excesivos
        per_doc_limit = 600

        for i, doc in enumerate(documents, 1):
            raw_content = doc.get('content', '') or ''
            # Recortar a per_doc_limit caracteres
            snippet = raw_content.strip()
            if len(snippet) > per_doc_limit:
                snippet = snippet[:per_doc_limit].rsplit(' ', 1)[0] + '...'

            # Intentar obtener una URL o nombre de fuente en metadatos
            metadata = doc.get('metadata', {}) or {}
            source = metadata.get('source_url') or metadata.get('source_path') or metadata.get('source_file') or 'Desconocido'

            doc_text = f"\n\n[{i}] Fuente: {source}\n{snippet}"

            if current_length + len(doc_text) > max_length:
                break

            context_parts.append(doc_text)
            current_length += len(doc_text)

        return "".join(context_parts)
    
    def _format_results(self, raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formatea los resultados de ChromaDB
        
        Args:
            raw_results: Resultados crudos de ChromaDB
            
        Returns:
            Lista de documentos formateados
        """
        documents = []
        
        docs = raw_results.get('documents', [[]])[0]
        metadatas = raw_results.get('metadatas', [[]])[0]
        distances = raw_results.get('distances', [[]])[0]
        
        for i, (doc, metadata, distance) in enumerate(zip(docs, metadatas, distances)):
            documents.append({
                'content': doc,
                'metadata': metadata,
                'distance': distance,
                'relevance_score': 1 - distance,  # Convertir distancia a score
                'rank': i + 1
            })
        
        return documents
    
    def _build_context(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Construye un contexto completo para el LLM
        
        Args:
            query: Consulta actual
            documents: Documentos recuperados
            conversation_history: Historial opcional
            
        Returns:
            Dict con el contexto completo
        """
        # Contexto de documentos
        doc_context = self._format_documents_for_llm(documents)
        
        # Contexto de conversación
        conv_context = ""
        if conversation_history:
            conv_context = self._format_conversation_history(conversation_history)
        
        return {
            'query': query,
            'document_context': doc_context,
            'conversation_context': conv_context,
            'documents_count': len(documents),
            'has_conversation': bool(conversation_history)
        }
    
    def _format_documents_for_llm(self, documents: List[Dict[str, Any]]) -> str:
        """
        Formatea documentos para incluir en el prompt del LLM
        
        Args:
            documents: Lista de documentos
            
        Returns:
            Texto formateado
        """
        if not documents:
            return "No se encontró información relevante."
        
        parts = ["INFORMACIÓN DE LA BASE DE CONOCIMIENTOS:"]
        
        for i, doc in enumerate(documents, 1):
            source = doc['metadata'].get('source_file', 'Desconocido')
            content = doc['content']
            score = doc.get('relevance_score', 0)
            
            parts.append(f"\n\n[Documento {i}] (Fuente: {source}, Relevancia: {score:.2f})")
            parts.append(f"\n{content}")
        
        return "".join(parts)
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """
        Formatea el historial de conversación
        
        Args:
            history: Lista de mensajes
            
        Returns:
            Texto formateado
        """
        if not history:
            return ""
        
        parts = ["HISTORIAL DE CONVERSACIÓN:"]
        
        for msg in history[-5:]:  # Últimos 5 mensajes
            rol = msg.get('rol', 'unknown')
            contenido = msg.get('contenido', '')
            parts.append(f"\n{rol.upper()}: {contenido}")
        
        return "".join(parts)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la colección
        
        Returns:
            Dict con estadísticas
        """
        stats = self.vector_store.get_collection_stats()
        model_info = self.document_processor.get_model_info()
        
        return {
            **stats,
            **model_info
        }


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
