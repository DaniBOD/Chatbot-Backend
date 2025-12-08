"""
Script para probar el chatbot desde la terminal
Permite iniciar conversaciones y enviar mensajes
"""
import os
import sys
import django
import uuid

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django (el módulo se llama Core-Backend)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core-Backend.settings')
django.setup()

from ModuloEmergencia.services.chatbot_service import ChatbotService
from ModuloEmergencia.models import ChatConversation, ChatMessage

def print_separator():
    print("\n" + "="*70 + "\n")

def print_message(rol, mensaje):
    emoji = "👤" if rol == "usuario" else "🤖"
    print(f"{emoji} {rol.upper()}: {mensaje}")
    print()

def main():
    print("="*70)
    print("🤖 CHATBOT DE EMERGENCIAS - PRUEBA EN TERMINAL")
    print("="*70)
    print("\nComandos disponibles:")
    print("  - Escribe 'salir' o 'exit' para terminar")
    print("  - Escribe 'nueva' para iniciar nueva conversación")
    print("  - Escribe 'historial' para ver el historial completo")
    print("  - Escribe 'datos' para ver datos recolectados")
    print_separator()
    
    service = ChatbotService()
    session_id = None
    conversation = None
    
    # Iniciar primera conversación
    print("🚀 Iniciando nueva conversación...")
    session_id = str(uuid.uuid4())
    conversation, mensaje_inicial = service.start_conversation(session_id)
    print_message("asistente", mensaje_inicial)
    
    while True:
        try:
            # Leer input del usuario
            user_input = input("👤 Tú: ").strip()
            
            if not user_input:
                continue
            
            # Comandos especiales
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                break
            
            elif user_input.lower() == 'nueva':
                print_separator()
                print("🚀 Iniciando nueva conversación...")
                session_id = str(uuid.uuid4())
                conversation, mensaje_inicial = service.start_conversation(session_id)
                print_message("asistente", mensaje_inicial)
                continue
            
            elif user_input.lower() == 'historial':
                if conversation:
                    print_separator()
                    print("📜 HISTORIAL DE CONVERSACIÓN")
                    print_separator()
                    messages = ChatMessage.objects.filter(
                        conversation=conversation
                    ).order_by('timestamp')
                    for msg in messages:
                        print_message(msg.rol, msg.contenido)
                    print_separator()
                continue
            
            elif user_input.lower() == 'datos':
                if conversation:
                    conversation.refresh_from_db()
                    print_separator()
                    print("📊 DATOS RECOLECTADOS")
                    print_separator()
                    datos = conversation.datos_recolectados
                    if datos:
                        for key, value in datos.items():
                            print(f"  ✓ {key}: {value}")
                    else:
                        print("  (No hay datos recolectados aún)")
                    print(f"\n  Estado: {conversation.estado}")
                    print_separator()
                continue
            
            # Procesar mensaje normal
            if not session_id:
                print("⚠️  No hay conversación activa. Escribe 'nueva' para iniciar.")
                continue
            
            response = service.process_message(session_id, user_input)
            
            if 'error' in response:
                print(f"\n⚠️  Error: {response.get('message', 'Error desconocido')}\n")
            else:
                print_message("asistente", response['message'])
                
                # Mostrar info adicional si está disponible
                if response.get('datos_faltantes'):
                    faltantes = len(response['datos_faltantes'])
                    print(f"ℹ️  Faltan {faltantes} datos por recolectar\n")
                
                if response.get('completed'):
                    print("✅ Conversación completada!\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrumpido por el usuario. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
