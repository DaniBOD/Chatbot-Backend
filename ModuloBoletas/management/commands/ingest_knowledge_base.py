"""
Management command para poblar la base de conocimientos RAG con documentos.

Uso:
    python manage.py ingest_knowledge_base                # Ingesta incremental
    python manage.py ingest_knowledge_base --reset        # Resetea y vuelve a ingerir
    python manage.py ingest_knowledge_base --stats        # Muestra estadísticas solamente
"""

from django.core.management.base import BaseCommand, CommandError
from ModuloBoletas.RAG.ingest_documents import get_document_ingester, initialize_knowledge_base
from ModuloBoletas.RAG.retriever import get_rag_retriever
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ingesta documentos de la base de conocimientos en el vector store'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Resetea la colección antes de ingerir (elimina todos los documentos existentes)',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Muestra estadísticas de la colección sin ingerir',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada del proceso',
        )

    def handle(self, *args, **options):
        # Configurar nivel de logging
        if options['verbose']:
            logger.setLevel(logging.DEBUG)
        
        # Obtener instancias
        ingester = get_document_ingester()
        retriever = get_rag_retriever()
        
        # Modo estadísticas
        if options['stats']:
            self.stdout.write(self.style.HTTP_INFO('\n📊 Estadísticas de la base de conocimientos:\n'))
            stats = retriever.get_collection_stats()
            
            self.stdout.write(f"  🗄️  Colección: {stats.get('collection_name', 'N/A')}")
            self.stdout.write(f"  📄 Documentos: {stats.get('document_count', 0)}")
            self.stdout.write(f"  ✅ Estado: {stats.get('status', 'N/A')}")
            
            # Información del processor
            processor_info = stats.get('processor_info', {})
            if processor_info:
                self.stdout.write(f"\n  🔧 Configuración del processor:")
                self.stdout.write(f"     - Chunk size: {processor_info.get('chunk_size', 'N/A')}")
                self.stdout.write(f"     - Chunk overlap: {processor_info.get('chunk_overlap', 'N/A')}")
                self.stdout.write(f"     - Modelo: {processor_info.get('embedding_model', 'N/A')}")
            
            self.stdout.write(self.style.SUCCESS('\n✅ Estadísticas obtenidas correctamente\n'))
            return
        
        # Ingesta de documentos
        force_reset = options['reset']
        
        if force_reset:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  Modo RESET activado: Se eliminarán todos los documentos existentes\n'
                )
            )
            confirm = input('¿Estás seguro? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('❌ Operación cancelada\n'))
                return
        
        self.stdout.write(
            self.style.HTTP_INFO(
                f'\n🚀 Iniciando ingesta de documentos (force_reset={force_reset})...\n'
            )
        )
        
        try:
            # Ejecutar ingesta
            result = initialize_knowledge_base(force_reset=force_reset)
            
            # Mostrar resultados
            if result['success']:
                self.stdout.write(self.style.SUCCESS('\n✅ Ingesta completada exitosamente!\n'))
                self.stdout.write(f"  📁 Archivos procesados: {result['files_processed']}")
                self.stdout.write(f"  📄 Chunks generados: {result['chunks_generated']}")
                self.stdout.write(f"  💾 Documentos agregados: {result['documents_added']}")
                
                # Obtener estadísticas finales
                self.stdout.write(self.style.HTTP_INFO('\n📊 Estadísticas finales:\n'))
                stats = retriever.get_collection_stats()
                self.stdout.write(f"  🗄️  Colección: {stats.get('collection_name', 'N/A')}")
                self.stdout.write(f"  📄 Total documentos: {stats.get('document_count', 0)}")
                self.stdout.write(f"  ✅ Estado: {stats.get('status', 'N/A')}")
                
                self.stdout.write(
                    self.style.SUCCESS(
                        '\n🎉 Base de conocimientos lista para usar!\n'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'\n❌ Error durante la ingesta: {result.get("error", "Error desconocido")}\n'
                    )
                )
                raise CommandError('Ingesta fallida')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error inesperado: {str(e)}\n')
            )
            logger.exception("Error durante la ingesta")
            raise CommandError(f'Error durante la ingesta: {str(e)}')
