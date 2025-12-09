"""
Terminal Interactiva para Probar ModuloBoletas en Local
Ejecuta conversaciones simuladas con el chatbot sin necesidad de API REST
"""
import os
import django
import sys
from datetime import date
from decimal import Decimal

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core-Backend.settings')
django.setup()

from ModuloBoletas.models import Boleta, ChatConversation, ChatMessage
from ModuloBoletas.services.chatbot_service import ChatbotService
import uuid


class BoletasTerminal:
    """Terminal interactiva para probar el módulo de boletas"""
    
    def __init__(self):
        self.service = ChatbotService()
        self.session_id = None
        self.conversation = None
    
    def mostrar_banner(self):
        """Muestra el banner de bienvenida"""
        print("\n" + "="*80)
        print(" 🤖 TERMINAL INTERACTIVA - MÓDULO DE BOLETAS ".center(80, "="))
        print("="*80)
        print("""
Este ejecutable te permite probar el chatbot de boletas directamente en la terminal.

💡 COMANDOS DISPONIBLES (opcionales):
   /boletas     - Ver boletas disponibles en BD
   /stats       - Ver estadísticas del sistema
   /nueva       - Reiniciar conversación
   /salir       - Salir del programa

📝 USO:
   Simplemente escribe tus consultas y el bot responderá.
   La conversación se inicia automáticamente.

🎯 EJEMPLOS DE CONSULTAS:
   • "Hola, quiero ver mi boleta. RUT 12345678-9"
   • "Necesito saber cuánto debo pagar, mi RUT es 98765432-1"
   • "Quiero comparar mis consumos, RUT 11111111-1"
   • "¿Cómo se calcula el monto de la boleta?"
        """)
        print("="*80 + "\n")
    
    def mostrar_boletas_disponibles(self):
        """Muestra las boletas disponibles en la BD"""
        print("\n📊 BOLETAS DISPONIBLES EN BASE DE DATOS\n")
        
        boletas = Boleta.objects.all()
        if not boletas.exists():
            print("⚠️  No hay boletas en la base de datos")
            print("💡 Ejecuta: python poblar_boletas.py\n")
            return
        
        # Agrupar por usuario
        usuarios = {}
        for boleta in boletas:
            if boleta.rut not in usuarios:
                usuarios[boleta.rut] = {
                    'nombre': boleta.nombre,
                    'direccion': boleta.direccion,
                    'boletas': []
                }
            usuarios[boleta.rut]['boletas'].append(boleta)
        
        # Mostrar
        for rut, data in usuarios.items():
            print(f"👤 {data['nombre']} ({rut})")
            print(f"   📍 {data['direccion']}")
            print(f"   📄 {len(data['boletas'])} boletas registradas")
            
            # Última boleta
            ultima = sorted(data['boletas'], key=lambda b: b.fecha_emision, reverse=True)[0]
            estado_emoji = {
                'pagada': '✅',
                'pendiente': '⏳',
                'vencida': '⚠️',
                'anulada': '❌'
            }
            emoji = estado_emoji.get(ultima.estado_pago, '📄')
            
            print(f"   {emoji} Última: {ultima.periodo_facturacion} - "
                  f"{ultima.consumo} m³ - ${ultima.monto:,.0f} ({ultima.estado_pago})\n")
        
        print(f"📊 Total: {boletas.count()} boletas\n")
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas del sistema"""
        print("\n📊 ESTADÍSTICAS DEL SISTEMA\n")
        
        total_boletas = Boleta.objects.count()
        total_conversaciones = ChatConversation.objects.count()
        total_mensajes = ChatMessage.objects.count()
        
        print(f"📄 Total de boletas: {total_boletas}")
        print(f"💬 Total de conversaciones: {total_conversaciones}")
        print(f"📝 Total de mensajes: {total_mensajes}")
        
        if total_boletas > 0:
            print("\n📋 Por estado de pago:")
            for estado in ['pagada', 'pendiente', 'vencida', 'anulada']:
                count = Boleta.objects.filter(estado_pago=estado).count()
                porcentaje = (count / total_boletas * 100) if total_boletas > 0 else 0
                print(f"   • {estado.capitalize()}: {count} ({porcentaje:.1f}%)")
            
            print("\n💰 Estadísticas de monto:")
            montos = [float(b.monto) for b in Boleta.objects.all()]
            print(f"   • Promedio: ${sum(montos)/len(montos):,.0f}")
            print(f"   • Mínimo: ${min(montos):,.0f}")
            print(f"   • Máximo: ${max(montos):,.0f}")
        
        print()
    
    def limpiar_conversaciones(self):
        """Limpia conversaciones antiguas"""
        print("\n🗑️  LIMPIEZA DE CONVERSACIONES\n")
        
        count = ChatConversation.objects.count()
        if count == 0:
            print("✅ No hay conversaciones para limpiar\n")
            return
        
        confirmacion = input(f"⚠️  Se eliminarán {count} conversaciones. ¿Continuar? (s/N): ")
        if confirmacion.lower() == 's':
            ChatConversation.objects.all().delete()
            print(f"✅ {count} conversaciones eliminadas\n")
        else:
            print("❌ Operación cancelada\n")
    
    def nueva_conversacion(self):
        """Inicia una nueva conversación"""
        self.session_id = str(uuid.uuid4())
        
        print("\n" + "="*80)
        print(" 🆕 INICIANDO CONVERSACIÓN ".center(80, "="))
        print("="*80 + "\n")
        
        try:
            self.conversation, mensaje = self.service.start_conversation(self.session_id)
            
            print(f"🔑 Session ID: {self.session_id}\n")
            print("─"*80 + "\n")
            print(f"🤖 Asistente:\n{mensaje}\n")
            print("─"*80 + "\n")
            
            return True
        except Exception as e:
            print(f"❌ Error iniciando conversación: {e}\n")
            return False
    
    def procesar_mensaje(self, mensaje: str):
        """Procesa un mensaje del usuario"""
        if not self.session_id:
            print("⚠️  Error: No hay sesión activa. Reiniciando...\n")
            if not self.nueva_conversacion():
                print("❌ No se pudo reiniciar la conversación\n")
                return
        
        print("─"*80 + "\n")
        print(f"👤 Tú:\n{mensaje}\n")
        print("─"*80 + "\n")
        
        try:
            response = self.service.process_message(self.session_id, mensaje)
            
            print(f"🤖 Asistente:\n{response.get('message', response.get('error', 'Sin respuesta'))}\n")
            
            # Mostrar metadata si es relevante
            if response.get('boleta_id'):
                print(f"📄 Boleta encontrada: {response['boleta_id']}")
            
            if response.get('es_consulta_comparativa'):
                print("📊 Consulta comparativa detectada")
            
            print(f"📊 Estado: {response.get('estado', 'desconocido')}")
            
            if response.get('completed'):
                print("✅ Consulta completada")
            
            print()
            
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}\n")
    
    def mostrar_ayuda(self):
        """Muestra la ayuda"""
        print("""
📖 AYUDA - COMANDOS DISPONIBLES

/nueva       - Iniciar nueva conversación con el chatbot
/boletas     - Ver lista de boletas disponibles en la base de datos
/stats       - Mostrar estadísticas del sistema (boletas, conversaciones, etc.)
/limpiar     - Eliminar todas las conversaciones guardadas
/help        - Mostrar esta ayuda
/salir       - Salir del programa

💬 CONVERSACIÓN:
Una vez iniciada una conversación con /nueva, simplemente escribe tus mensajes
y el chatbot responderá. No es necesario usar comandos, escribe naturalmente.

🎯 EJEMPLOS:
   • "Hola, quiero consultar mi boleta. Mi RUT es 12345678-9"
   • "Cuánto debo pagar?"
   • "Quiero comparar mis consumos de los últimos meses"
   • "¿Cómo se calcula el monto?"
   • "¿Qué pasa si no puedo pagar a tiempo?"

💡 TIPS:
   • Puedes proporcionar tu RUT en cualquier momento
   • El bot recuerda tu boleta durante la conversación
   • Puedes hacer múltiples preguntas en la misma sesión
   • Usa /nueva para comenzar una conversación fresca
        """)
    
    def ejecutar(self):
        """Ejecuta el loop principal de la terminal"""
        self.mostrar_banner()
        
        # Iniciar automáticamente una nueva conversación
        if not self.nueva_conversacion():
            print("❌ No se pudo iniciar la conversación. Saliendo...\n")
            return
        
        while True:
            try:
                # Prompt
                if self.session_id:
                    prompt = "💬 > "
                else:
                    prompt = "⚪ > "
                
                entrada = input(prompt).strip()
                
                if not entrada:
                    continue
                
                # Procesar comandos
                if entrada.startswith('/'):
                    comando = entrada.lower()
                    
                    if comando == '/salir':
                        print("\n👋 ¡Hasta luego!\n")
                        break
                    
                    elif comando == '/nueva':
                        self.nueva_conversacion()
                    
                    elif comando == '/boletas':
                        self.mostrar_boletas_disponibles()
                    
                    elif comando == '/stats':
                        self.mostrar_estadisticas()
                    
                    elif comando == '/limpiar':
                        self.limpiar_conversaciones()
                    
                    elif comando == '/help':
                        self.mostrar_ayuda()
                    
                    else:
                        print(f"❌ Comando desconocido: {comando}")
                        print("💡 Usa /help para ver comandos disponibles\n")
                
                else:
                    # Procesar mensaje normal
                    self.procesar_mensaje(entrada)
            
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!\n")
                break
            
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


def main():
    """Función principal"""
    terminal = BoletasTerminal()
    terminal.ejecutar()


if __name__ == '__main__':
    main()
