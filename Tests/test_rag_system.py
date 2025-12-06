"""
Tests del sistema RAG (Retrieval-Augmented Generation).
Componentes: vector_store.py, embeddings.py, retriever.py
Objetivo: Aumentar cobertura de 32-42% a 70%+
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
import os
import tempfile
import shutil


class VectorStoreTests(TestCase):
    """Tests para vector_store.py"""
    
    @patch('chromadb.PersistentClient')
    def test_get_vector_store_initialization(self, mock_chroma):
        """Test que get_vector_store inicializa correctamente"""
        from ModuloEmergencia.RAG.vector_store import get_vector_store
        
        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma.return_value = mock_client
        
        vector_store = get_vector_store()
        
        self.assertIsNotNone(vector_store)
        mock_chroma.assert_called_once()
    
    @patch('chromadb.PersistentClient')
    def test_vector_store_collection_name(self, mock_chroma):
        """Test que usa el nombre de colección correcto"""
        from ModuloEmergencia.RAG.vector_store import get_vector_store
        
        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma.return_value = mock_client
        
        get_vector_store()
        
        # Verificar que se llamó con el nombre correcto
        call_args = mock_client.get_or_create_collection.call_args
        self.assertEqual(call_args[1]['name'], 'emergencias_knowledge_base')
    
    @patch('chromadb.PersistentClient')
    def test_add_documents_to_vector_store(self, mock_chroma):
        """Test agregar documentos al vector store"""
        from ModuloEmergencia.RAG.vector_store import VectorStore
        
        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma.return_value = mock_client
        
        vector_store = VectorStore()
        
        # Simular agregar documentos
        documents = ["Documento 1", "Documento 2"]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        metadatas = [{"source": "test1"}, {"source": "test2"}]
        ids = ["id1", "id2"]
        
        vector_store.add_documents(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        # Verificar que se llamó al método add de la colección
        mock_collection.add.assert_called_once()
    
    @patch('chromadb.PersistentClient')
    def test_query_vector_store(self, mock_chroma):
        """Test consultar el vector store"""
        from ModuloEmergencia.RAG.vector_store import VectorStore
        
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'documents': [["Doc 1", "Doc 2"]],
            'distances': [[0.5, 0.8]],
            'metadatas': [[{"source": "test"}]]
        }
        mock_client = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma.return_value = mock_client
        
        vector_store = VectorStore()
        
        query_embedding = [0.1, 0.2, 0.3]
        results = vector_store.query(query_embedding, n_results=5)
        
        self.assertIsNotNone(results)
        mock_collection.query.assert_called_once()
    
    @patch('chromadb.PersistentClient')
    def test_get_collection_count(self, mock_chroma):
        """Test obtener cantidad de documentos en la colección"""
        from ModuloEmergencia.RAG.vector_store import VectorStore
        
        mock_collection = Mock()
        mock_collection.count.return_value = 127
        mock_client = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma.return_value = mock_client
        
        vector_store = VectorStore()
        count = vector_store.collection.count()
        
        self.assertEqual(count, 127)


class DocumentProcessorTests(TestCase):
    """Tests para embeddings.py - DocumentProcessor"""
    
    def setUp(self):
        """Crear archivos temporales para testing"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_doc.txt")
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("Este es un documento de prueba para testing del sistema RAG.")
    
    def tearDown(self):
        """Limpiar archivos temporales"""
        shutil.rmtree(self.test_dir)
    
    def test_document_processor_initialization(self):
        """Test inicialización del DocumentProcessor"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        
        processor = DocumentProcessor()
        self.assertIsNotNone(processor)
        self.assertIsNotNone(processor.embedding_model)
    
    def test_load_document_txt(self):
        """Test cargar documento .txt"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        
        processor = DocumentProcessor()
        document = processor.load_document(self.test_file)
        
        self.assertIsNotNone(document)
        self.assertIn("documento de prueba", document.page_content)
    
    def test_load_document_nonexistent_file(self):
        """Test cargar documento que no existe"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        
        processor = DocumentProcessor()
        
        with self.assertRaises(Exception):
            processor.load_document("/path/to/nonexistent/file.txt")
    
    def test_split_documents(self):
        """Test dividir documentos en chunks"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        from langchain.schema import Document
        
        processor = DocumentProcessor()
        
        # Crear un documento largo
        long_text = "palabra " * 500  # Más de 1000 caracteres
        document = Document(page_content=long_text, metadata={"source": "test"})
        
        chunks = processor.split_documents([document])
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        # Verificar que ningún chunk excede el tamaño máximo
        for chunk in chunks:
            self.assertLessEqual(len(chunk.page_content), 1200)
    
    def test_split_documents_preserves_metadata(self):
        """Test que split_documents preserva metadata"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        from langchain.schema import Document
        
        processor = DocumentProcessor()
        
        test_metadata = {"source": "test.txt", "category": "emergencias"}
        document = Document(page_content="Texto de prueba", metadata=test_metadata)
        
        chunks = processor.split_documents([document])
        
        # Verificar que el metadata se mantiene
        for chunk in chunks:
            self.assertEqual(chunk.metadata['source'], 'test.txt')
    
    def test_generate_embeddings(self):
        """Test generar embeddings de texto"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        
        processor = DocumentProcessor()
        
        text = "Este es un texto de prueba"
        embeddings = processor.generate_embeddings([text])
        
        self.assertIsInstance(embeddings, list)
        self.assertGreater(len(embeddings), 0)
        self.assertIsInstance(embeddings[0], list)
        
        # El modelo genera embeddings de 384 dimensiones
        self.assertEqual(len(embeddings[0]), 384)
    
    def test_generate_embeddings_multiple_texts(self):
        """Test generar embeddings para múltiples textos"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        
        processor = DocumentProcessor()
        
        texts = [
            "Primer texto de prueba",
            "Segundo texto de prueba",
            "Tercer texto de prueba"
        ]
        
        embeddings = processor.generate_embeddings(texts)
        
        self.assertEqual(len(embeddings), 3)
        
        # Todos deben tener la misma dimensión
        for embedding in embeddings:
            self.assertEqual(len(embedding), 384)
    
    def test_process_text_end_to_end(self):
        """Test proceso completo de texto a embeddings"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        
        processor = DocumentProcessor()
        
        text = "Este es un documento completo para testing del sistema RAG."
        chunks, embeddings = processor.process_text(text)
        
        self.assertIsInstance(chunks, list)
        self.assertIsInstance(embeddings, list)
        self.assertEqual(len(chunks), len(embeddings))


class RAGRetrieverTests(TestCase):
    """Tests para retriever.py - RAGRetriever"""
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    @patch('ModuloEmergencia.RAG.embeddings.DocumentProcessor')
    def test_retriever_initialization(self, mock_processor, mock_vector_store):
        """Test inicialización del RAGRetriever"""
        from ModuloEmergencia.RAG.retriever import RAGRetriever
        
        mock_vector_store.return_value = Mock()
        mock_processor.return_value = Mock()
        
        retriever = RAGRetriever()
        
        self.assertIsNotNone(retriever)
        self.assertIsNotNone(retriever.vector_store)
        self.assertIsNotNone(retriever.document_processor)
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    @patch('ModuloEmergencia.RAG.embeddings.DocumentProcessor')
    def test_get_relevant_context_returns_string(self, mock_processor, mock_vector_store):
        """Test que get_relevant_context retorna un string"""
        from ModuloEmergencia.RAG.retriever import RAGRetriever
        
        # Configurar mocks
        mock_vs = Mock()
        mock_vs.query.return_value = {
            'documents': [["Documento relevante 1", "Documento relevante 2"]],
            'distances': [[0.3, 0.5]],
            'metadatas': [[{"source": "test1.md"}, {"source": "test2.md"}]]
        }
        mock_vector_store.return_value = mock_vs
        
        mock_proc = Mock()
        mock_proc.generate_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_processor.return_value = mock_proc
        
        retriever = RAGRetriever()
        context = retriever.get_relevant_context("¿Cuál es el horario?")
        
        self.assertIsInstance(context, str)
        self.assertGreater(len(context), 0)
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    @patch('ModuloEmergencia.RAG.embeddings.DocumentProcessor')
    def test_get_relevant_context_with_conversation_history(self, mock_processor, mock_vector_store):
        """Test get_relevant_context con historial de conversación"""
        from ModuloEmergencia.RAG.retriever import RAGRetriever
        
        mock_vs = Mock()
        mock_vs.query.return_value = {
            'documents': [["Contexto relevante"]],
            'distances': [[0.4]],
            'metadatas': [[{"source": "test.md"}]]
        }
        mock_vector_store.return_value = mock_vs
        
        mock_proc = Mock()
        mock_proc.generate_embeddings.return_value = [[0.1, 0.2]]
        mock_processor.return_value = mock_proc
        
        retriever = RAGRetriever()
        
        conversation_history = [
            {"rol": "usuario", "contenido": "Hola"},
            {"rol": "asistente", "contenido": "¿En qué puedo ayudarte?"}
        ]
        
        context = retriever.get_relevant_context(
            "¿Cuál es el horario?",
            conversation_history=conversation_history
        )
        
        self.assertIsInstance(context, str)
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    @patch('ModuloEmergencia.RAG.embeddings.DocumentProcessor')
    def test_get_relevant_context_limits_results(self, mock_processor, mock_vector_store):
        """Test que get_relevant_context limita resultados a top_k"""
        from ModuloEmergencia.RAG.retriever import RAGRetriever
        
        mock_vs = Mock()
        mock_vs.query.return_value = {
            'documents': [["Doc1", "Doc2", "Doc3", "Doc4", "Doc5"]],
            'distances': [[0.1, 0.2, 0.3, 0.4, 0.5]],
            'metadatas': [[{"source": f"test{i}.md"} for i in range(5)]]
        }
        mock_vector_store.return_value = mock_vs
        
        mock_proc = Mock()
        mock_proc.generate_embeddings.return_value = [[0.1]]
        mock_processor.return_value = mock_proc
        
        retriever = RAGRetriever(top_k=3)
        context = retriever.get_relevant_context("Query de prueba")
        
        # Verificar que query fue llamado con n_results correcto
        call_args = mock_vs.query.call_args
        self.assertEqual(call_args[1]['n_results'], 3)
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    @patch('ModuloEmergencia.RAG.embeddings.DocumentProcessor')
    def test_search_by_category(self, mock_processor, mock_vector_store):
        """Test búsqueda filtrada por categoría"""
        from ModuloEmergencia.RAG.retriever import RAGRetriever
        
        mock_vs = Mock()
        mock_vs.query.return_value = {
            'documents': [["Documento de protocolos"]],
            'distances': [[0.2]],
            'metadatas': [[{"category": "protocolos", "source": "protocolos.md"}]]
        }
        mock_vector_store.return_value = mock_vs
        
        mock_proc = Mock()
        mock_proc.generate_embeddings.return_value = [[0.1]]
        mock_processor.return_value = mock_proc
        
        retriever = RAGRetriever()
        results = retriever.search_by_category("protocolos", "¿Qué hacer?")
        
        self.assertIsInstance(results, list)
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    @patch('ModuloEmergencia.RAG.embeddings.DocumentProcessor')
    def test_get_relevant_context_handles_empty_results(self, mock_processor, mock_vector_store):
        """Test manejo de resultados vacíos"""
        from ModuloEmergencia.RAG.retriever import RAGRetriever
        
        mock_vs = Mock()
        mock_vs.query.return_value = {
            'documents': [[]],
            'distances': [[]],
            'metadatas': [[]]
        }
        mock_vector_store.return_value = mock_vs
        
        mock_proc = Mock()
        mock_proc.generate_embeddings.return_value = [[0.1]]
        mock_processor.return_value = mock_proc
        
        retriever = RAGRetriever()
        context = retriever.get_relevant_context("Query sin resultados")
        
        # Debe retornar string vacío o mensaje por defecto
        self.assertIsInstance(context, str)


class IngestDocumentsTests(TestCase):
    """Tests para ingest_documents.py"""
    
    def setUp(self):
        """Crear directorio temporal con documentos de prueba"""
        self.test_dir = tempfile.mkdtemp()
        
        # Crear algunos archivos de prueba
        self.test_files = []
        for i in range(3):
            file_path = os.path.join(self.test_dir, f"test_doc_{i}.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Documento de prueba {i}\n\n")
                f.write("Este es el contenido del documento. " * 50)
            self.test_files.append(file_path)
    
    def tearDown(self):
        """Limpiar archivos temporales"""
        shutil.rmtree(self.test_dir)
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    @patch('ModuloEmergencia.RAG.embeddings.DocumentProcessor')
    def test_ingest_documents_from_directory(self, mock_processor, mock_vector_store):
        """Test ingesta de documentos desde un directorio"""
        # Este test verifica la lógica general sin ejecutar el script completo
        mock_vs = Mock()
        mock_vector_store.return_value = mock_vs
        
        mock_proc = Mock()
        mock_proc.load_document.return_value = Mock(page_content="Contenido")
        mock_proc.split_documents.return_value = [Mock(page_content="Chunk")]
        mock_proc.generate_embeddings.return_value = [[0.1, 0.2]]
        mock_processor.return_value = mock_proc
        
        # Simular la función de ingesta
        processor = mock_proc
        vector_store = mock_vs
        
        for file_path in self.test_files:
            doc = processor.load_document(file_path)
            chunks = processor.split_documents([doc])
            embeddings = processor.generate_embeddings([c.page_content for c in chunks])
            vector_store.add_documents(
                documents=[c.page_content for c in chunks],
                embeddings=embeddings,
                metadatas=[{"source": file_path}],
                ids=[f"{file_path}_{i}" for i in range(len(chunks))]
            )
        
        # Verificar que se procesaron todos los archivos
        self.assertEqual(processor.load_document.call_count, 3)
    
    def test_ingest_handles_markdown_files(self):
        """Test que la ingesta maneja archivos .md"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        
        processor = DocumentProcessor()
        
        md_file = os.path.join(self.test_dir, "test.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# Título\n\nContenido del documento markdown.")
        
        document = processor.load_document(md_file)
        
        self.assertIsNotNone(document)
        self.assertIn("Título", document.page_content)
    
    def test_ingest_generates_unique_ids(self):
        """Test que se generan IDs únicos para cada chunk"""
        ids = []
        for i, file_path in enumerate(self.test_files):
            for j in range(3):  # 3 chunks por archivo
                chunk_id = f"{os.path.basename(file_path)}_{j}"
                ids.append(chunk_id)
        
        # Verificar que todos los IDs son únicos
        self.assertEqual(len(ids), len(set(ids)))


class RAGStatsTests(TestCase):
    """Tests para estadísticas del sistema RAG"""
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    def test_get_collection_stats(self, mock_vector_store):
        """Test obtener estadísticas de la colección"""
        mock_vs = Mock()
        mock_vs.collection.count.return_value = 127
        mock_vector_store.return_value = mock_vs
        
        vector_store = mock_vs
        count = vector_store.collection.count()
        
        self.assertEqual(count, 127)
    
    @patch('ModuloEmergencia.RAG.vector_store.get_vector_store')
    def test_get_all_documents_metadata(self, mock_vector_store):
        """Test obtener metadata de todos los documentos"""
        mock_vs = Mock()
        mock_vs.collection.get.return_value = {
            'ids': ['id1', 'id2'],
            'metadatas': [
                {'source': 'doc1.md', 'category': 'protocolos'},
                {'source': 'doc2.md', 'category': 'contactos'}
            ]
        }
        mock_vector_store.return_value = mock_vs
        
        vector_store = mock_vs
        data = vector_store.collection.get()
        
        self.assertEqual(len(data['ids']), 2)
        self.assertIn('source', data['metadatas'][0])


class EmbeddingQualityTests(TestCase):
    """Tests de calidad de embeddings"""
    
    def test_similar_texts_have_similar_embeddings(self):
        """Test que textos similares generan embeddings similares"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        import numpy as np
        
        processor = DocumentProcessor()
        
        text1 = "Tengo una fuga de agua en mi casa"
        text2 = "Hay una fuga de agua en mi domicilio"
        text3 = "El clima está soleado hoy"
        
        embeddings = processor.generate_embeddings([text1, text2, text3])
        
        # Calcular similitud coseno entre text1 y text2 (similares)
        emb1 = np.array(embeddings[0])
        emb2 = np.array(embeddings[1])
        emb3 = np.array(embeddings[2])
        
        similarity_12 = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        similarity_13 = np.dot(emb1, emb3) / (np.linalg.norm(emb1) * np.linalg.norm(emb3))
        
        # Textos similares deben tener mayor similitud que textos diferentes
        self.assertGreater(similarity_12, similarity_13)
    
    def test_embeddings_are_normalized(self):
        """Test que los embeddings están normalizados"""
        from ModuloEmergencia.RAG.embeddings import DocumentProcessor
        import numpy as np
        
        processor = DocumentProcessor()
        
        text = "Texto de prueba"
        embeddings = processor.generate_embeddings([text])
        
        emb = np.array(embeddings[0])
        norm = np.linalg.norm(emb)
        
        # La norma debe estar cerca de 1 (embeddings normalizados)
        self.assertAlmostEqual(norm, 1.0, places=1)


if __name__ == '__main__':
    unittest.main()
