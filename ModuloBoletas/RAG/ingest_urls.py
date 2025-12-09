"""
Script para ingestar archivos recién creados en la knowledge_base usando DocumentIngester
Ejecutar desde la raíz del proyecto Backend:
    python ModuloBoletas/RAG/ingest_urls.py
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Mover ruta a la carpeta Backend para encontrar Core-Backend
sys.path.append(str(Path(__file__).resolve().parents[2]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core-Backend.settings')
django.setup()

from ModuloBoletas.RAG.ingest_documents import get_document_ingester
from pathlib import Path


def main():
    ingester = get_document_ingester()
    kb_dir = Path(__file__).parent / 'knowledge_base'

    files = [
        kb_dir / 'cooplacia_home.txt',
        kb_dir / 'cooplacia_facebook.txt'
    ]

    results = {}

    for f in files:
        if not f.exists():
            print(f"Archivo no encontrado: {f}")
            continue
        print(f"Ingestando: {f.name}...")
        res = ingester.ingest_single_file(str(f))
        print(f"  Resultado: {res}")
        results[f.name] = res

    print('\nIngesta completa. Resumen:')
    for name, r in results.items():
        print(f" - {name}: {r}")


if __name__ == '__main__':
    main()
