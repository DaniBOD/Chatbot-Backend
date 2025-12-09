"""
Script de prueba para consultar el RAG y mostrar contexto relevante
Ejecutar desde la raíz del proyecto Backend:
    python ModuloBoletas/RAG/test_rag_query.py
"""
import os
import sys
from pathlib import Path
import django

# Setup Django
sys.path.append(str(Path(__file__).resolve().parents[2]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core-Backend.settings')
django.setup()

from ModuloBoletas.RAG.retriever import get_rag_retriever


def main():
    retriever = get_rag_retriever()
    query = "¿Cuál es el horario de atención de la cooperativa?"
    print(f"Query: {query}\n")
    context = retriever.get_relevant_context_text(query, max_length=2000)
    print("=== Contexto relevante obtenido ===\n")
    print(context)


if __name__ == '__main__':
    main()
