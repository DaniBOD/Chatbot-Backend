"""
Script de simulación del chatbot de boletas
Muestra ejemplos de las respuestas que genera la IA con RAG
"""
import os
import django
import sys
from datetime import date, timedelta
from decimal import Decimal

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout.reconfigure(encoding='utf-8')

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core-Backend.settings')
django.setup()

from ModuloBoletas.models import Boleta, ChatConversation, ChatMessage
from ModuloBoletas.services.chatbot_service import ChatbotService
import uuid


def limpiar_datos_prueba():
    """Limpia conversaciones y boletas de prueba"""
    print("\n🧹 Limpiando datos de prueba anteriores...")
    ChatConversation.objects.filter(session_id__contains='simulacion').delete()
    Boleta.objects.filter(rut='12345678-9').delete()
    print("✅ Datos de prueba limpios\n")


def crear_boletas_prueba():
    """Crea boletas de prueba para simulación"""
    print("📝 Creando boletas de prueba...")
    
    # Boleta actual (diciembre 2024) - consumo normal
    boleta1 = Boleta.objects.create(
        rut='12345678-9',
        nombre='Juan Pérez Ejemplo',
        direccion='Calle Principal 123, Santiago',
        periodo_facturacion='2024-12',
        fecha_emision=date(2024, 12, 5),
        fecha_vencimiento=date.today() + timedelta(days=15),
        consumo=Decimal('15.5'),
        lectura_anterior=Decimal('1234.0'),
        lectura_actual=Decimal('1249.5'),
        monto=Decimal('15667.50'),
        estado_pago='pendiente'
    )
    
    # Boleta anterior (noviembre 2024) - consumo similar
    boleta2 = Boleta.objects.create(
        rut='12345678-9',
        nombre='Juan Pérez Ejemplo',
        direccion='Calle Principal 123, Santiago',
        periodo_facturacion='2024-11',
        fecha_emision=date(2024, 11, 5),
        fecha_vencimiento=date(2024, 11, 25),
        consumo=Decimal('14.0'),
        lectura_anterior=Decimal('1220.0'),
        lectura_actual=Decimal('1234.0'),
        monto=Decimal('14400.00'),
        estado_pago='pagada'
    )
    
    # Boleta octubre 2024 - consumo alto (verano)
    boleta3 = Boleta.objects.create(
        rut='12345678-9',
        nombre='Juan Pérez Ejemplo',
        direccion='Calle Principal 123, Santiago',
        periodo_facturacion='2024-10',
        fecha_emision=date(2024, 10, 5),
        fecha_vencimiento=date(2024, 10, 25),
        consumo=Decimal('22.5'),
        lectura_anterior=Decimal('1197.5'),
        lectura_actual=Decimal('1220.0'),
        monto=Decimal('21625.00'),
        estado_pago='pagada'
    )
    
    print(f"✅ Creadas 3 boletas para RUT 12345678-9")
    print(f"   - Diciembre 2024: {boleta1.consumo} m³ - ${boleta1.monto} ({boleta1.estado_pago})")
    print(f"   - Noviembre 2024: {boleta2.consumo} m³ - ${boleta2.monto} ({boleta2.estado_pago})")
    print(f"   - Octubre 2024: {boleta3.consumo} m³ - ${boleta3.monto} ({boleta3.estado_pago})")
    print()
    
    return [boleta1, boleta2, boleta3]


def simular_conversacion(session_id, mensajes_usuario):
    """
    Simula una conversación completa con el chatbot
    
    Args:
        session_id: ID de la sesión
        mensajes_usuario: Lista de mensajes a enviar
    """
    print("="*80)
    print(f"🤖 SIMULACIÓN DE CONVERSACIÓN - Session: {session_id}")
    print("="*80)
    
    service = ChatbotService()
    
    # Iniciar conversación
    print("\n1️⃣  INICIANDO CONVERSACIÓN\n")
    conversation, mensaje_inicial = service.start_conversation(session_id)
    print(f"🤖 Asistente: {mensaje_inicial}\n")
    print(f"📊 Estado: {conversation.estado}")
    print(f"📝 Datos recolectados: {conversation.datos_recolectados}\n")
    
    # Procesar cada mensaje
    for i, mensaje in enumerate(mensajes_usuario, start=2):
        print("-"*80)
        print(f"\n{i}️⃣  MENSAJE DEL USUARIO\n")
        print(f"👤 Usuario: {mensaje}\n")
        
        response = service.process_message(session_id, mensaje)
        
        print(f"🤖 Asistente: {response.get('message', response.get('error', 'Sin respuesta'))}\n")
        
        # Mostrar metadata de la respuesta
        print("📊 Metadata de respuesta:")
        print(f"   - Estado: {response.get('estado')}")
        print(f"   - Completado: {response.get('completed', False)}")
        
        if response.get('boleta_id'):
            print(f"   - Boleta ID: {response['boleta_id']}")
        
        if response.get('es_consulta_comparativa'):
            print(f"   - Es comparativa: Sí")
        
        # Recargar conversación para ver datos actualizados
        conversation.refresh_from_db()
        print(f"   - Datos recolectados: {conversation.datos_recolectados}")
        print()


def main():
    """Función principal de simulación"""
    print("\n" + "="*80)
    print(" SIMULADOR DE CHATBOT DE BOLETAS - Análisis de Respuestas IA + RAG ".center(80))
    print("="*80 + "\n")
    
    # Preparar datos
    limpiar_datos_prueba()
    boletas = crear_boletas_prueba()
    
    print("\n" + "🎯 ESCENARIOS DE SIMULACIÓN".center(80, "="))
    print()
    
    # ============================================================================
    # ESCENARIO 1: Consulta simple de monto
    # ============================================================================
    print("\n📋 ESCENARIO 1: Consulta Simple de Monto")
    print("Objetivo: Usuario quiere saber cuánto debe pagar")
    print()
    
    simular_conversacion(
        session_id='simulacion-1-monto',
        mensajes_usuario=[
            "Hola, quiero saber cuánto debo pagar este mes. Mi RUT es 12345678-9"
        ]
    )
    
    # ============================================================================
    # ESCENARIO 2: Consulta de consumo
    # ============================================================================
    print("\n\n📋 ESCENARIO 2: Consulta de Consumo")
    print("Objetivo: Usuario quiere ver su consumo actual")
    print()
    
    simular_conversacion(
        session_id='simulacion-2-consumo',
        mensajes_usuario=[
            "Necesito saber mi consumo de agua, RUT 12345678-9"
        ]
    )
    
    # ============================================================================
    # ESCENARIO 3: Comparación de períodos
    # ============================================================================
    print("\n\n📋 ESCENARIO 3: Comparación de Períodos")
    print("Objetivo: Usuario quiere comparar consumos de diferentes meses")
    print()
    
    simular_conversacion(
        session_id='simulacion-3-comparacion',
        mensajes_usuario=[
            "Hola, quiero comparar mis consumos de los últimos meses. Mi RUT es 12345678-9"
        ]
    )
    
    # ============================================================================
    # ESCENARIO 4: Conversación multi-turno con preguntas adicionales
    # ============================================================================
    print("\n\n📋 ESCENARIO 4: Conversación Multi-Turno con RAG")
    print("Objetivo: Usuario hace preguntas que requieren conocimiento del RAG")
    print()
    
    simular_conversacion(
        session_id='simulacion-4-rag',
        mensajes_usuario=[
            "Hola, necesito información sobre mi boleta. RUT 12345678-9",
            "¿Mi consumo es normal?",
            "¿Qué pasa si no puedo pagar en la fecha de vencimiento?",
            "¿Cómo se calcula el monto que debo pagar?"
        ]
    )
    
    # ============================================================================
    # ESCENARIO 5: Estado de pago y fechas
    # ============================================================================
    print("\n\n📋 ESCENARIO 5: Estado de Pago y Fechas")
    print("Objetivo: Usuario pregunta por el estado y vencimiento")
    print()
    
    simular_conversacion(
        session_id='simulacion-5-estado',
        mensajes_usuario=[
            "Quiero verificar el estado de mi boleta, RUT 12345678-9",
            "¿Cuándo vence?"
        ]
    )
    
    # ============================================================================
    # Resumen final
    # ============================================================================
    print("\n\n" + "="*80)
    print(" RESUMEN DE LA SIMULACIÓN ".center(80))
    print("="*80)
    print("""
✅ Simulación completada exitosamente

📊 CAPACIDADES DEMOSTRADAS:
   1. Extracción de RUT y motivo de consulta con IA
   2. Búsqueda automática de boletas en BD
   3. Formateo de información clara con emojis
   4. Comparación inteligente de períodos
   5. Respuestas contextuales usando RAG (documentación de conocimiento)
   6. Conversaciones multi-turno manteniendo contexto
   7. Análisis de consumo con recomendaciones

🧠 FUENTES DE CONOCIMIENTO RAG:
   - guia_boletas.md: Explicación de componentes y consumos
   - preguntas_frecuentes.md: Respuestas a consultas comunes
   - tarifas.md: Cálculos de montos, recargos y subsidios

🎯 TIPOS DE RESPUESTA:
   - Consultas simples: Info directa formateada
   - Comparaciones: Análisis de tendencias con IA
   - Preguntas generales: Respuestas desde RAG
   - Multi-turno: Mantiene contexto de la boleta activa
    """)
    print("="*80 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Simulación interrumpida por el usuario\n")
    except Exception as e:
        print(f"\n\n❌ Error en la simulación: {e}\n")
        import traceback
        traceback.print_exc()
