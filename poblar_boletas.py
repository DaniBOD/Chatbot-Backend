"""
Script para poblar la base de datos con boletas simuladas
Crea datos realistas para pruebas y desarrollo del chatbot de boletas
"""
import os
import django
import sys
from datetime import date, timedelta
from decimal import Decimal
import random

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core-Backend.settings')
django.setup()

from ModuloBoletas.models import Boleta


# ============================================================================
# DATOS DE SIMULACIÓN
# ============================================================================

SECTORES = [
    'Anibana',
    'El Molino',
    'La Compañía',
    'El Maitén 1',
    'La Morera',
    'El Maitén 2',
    'Santa Margarita'
]

USUARIOS_SIMULADOS = [
    {'rut': '12345678-9', 'nombre': 'Juan Pérez González', 'direccion': 'Calle Los Robles 1234, Anibana'},
    {'rut': '98765432-1', 'nombre': 'María González López', 'direccion': 'Av. Principal 567, El Molino'},
    {'rut': '11111111-1', 'nombre': 'Pedro Rodríguez Silva', 'direccion': 'Pasaje Los Álamos 89, La Compañía'},
    {'rut': '22222222-2', 'nombre': 'Ana Martínez Rojas', 'direccion': 'Los Castaños 3450, El Maitén 1'},
    {'rut': '33333333-3', 'nombre': 'Carlos Sánchez Torres', 'direccion': 'Calle Las Acacias 234, La Morera'},
    {'rut': '44444444-4', 'nombre': 'Laura Fernández Díaz', 'direccion': 'Pasaje Los Pinos 678, El Maitén 2'},
    {'rut': '55555555-5', 'nombre': 'Roberto Castro Muñoz', 'direccion': 'Av. Los Olivos 1890, Santa Margarita'},
]

# Patrones de consumo por tipo de hogar
PATRONES_CONSUMO = {
    'bajo': (8, 12),      # Hogar pequeño, consciente del consumo
    'normal': (12, 18),   # Hogar promedio
    'alto': (18, 25),     # Hogar grande o con jardín
    'muy_alto': (25, 35)  # Hogar con piscina o consumo excesivo
}

# Estados de pago con probabilidades
ESTADOS_PAGO = [
    ('pagada', 0.70),     # 70% pagadas
    ('pendiente', 0.20),  # 20% pendientes
    ('vencida', 0.08),    # 8% vencidas
    ('anulada', 0.02)     # 2% anuladas
]

# Variabilidad estacional (por mes)
FACTOR_ESTACIONAL = {
    1: 0.85,   # Enero - vacaciones, menos consumo
    2: 0.90,   # Febrero
    3: 0.95,   # Marzo
    4: 1.00,   # Abril
    5: 1.05,   # Mayo
    6: 1.00,   # Junio
    7: 1.00,   # Julio
    8: 1.00,   # Agosto
    9: 1.05,   # Septiembre
    10: 1.15,  # Octubre - primavera, más riego
    11: 1.20,  # Noviembre - calor
    12: 1.25,  # Diciembre - verano, máximo consumo
}

# Configuración de tarifas
TARIFA_M3 = Decimal('850')        # $850 por m³
CARGO_FIJO = Decimal('2500')      # $2,500 cargo fijo
IVA = Decimal('0.19')             # 19% IVA


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def calcular_monto(consumo_m3: Decimal) -> Decimal:
    """Calcula el monto total de la boleta"""
    cargo_variable = consumo_m3 * TARIFA_M3
    subtotal = cargo_variable + CARGO_FIJO
    iva_monto = subtotal * IVA
    total = subtotal + iva_monto
    return total.quantize(Decimal('0.01'))


def generar_consumo_realista(mes: int, patron: str = 'normal', lectura_anterior: Decimal = None) -> tuple:
    """
    Genera consumo realista considerando estacionalidad y variabilidad
    
    Returns:
        tuple: (consumo, lectura_anterior, lectura_actual)
    """
    # Obtener rango base del patrón
    min_consumo, max_consumo = PATRONES_CONSUMO[patron]
    
    # Consumo base aleatorio dentro del rango
    consumo_base = random.uniform(min_consumo, max_consumo)
    
    # Aplicar factor estacional
    factor_mes = FACTOR_ESTACIONAL.get(mes, 1.0)
    consumo = consumo_base * factor_mes
    
    # Añadir variabilidad aleatoria (-10% a +15%)
    variabilidad = random.uniform(0.90, 1.15)
    consumo = consumo * variabilidad
    
    # Redondear a 1 decimal
    consumo = Decimal(str(round(consumo, 1)))
    
    # Generar lecturas
    if lectura_anterior is None:
        lectura_anterior = Decimal(str(random.randint(1000, 5000)))
    
    lectura_actual = lectura_anterior + consumo
    
    return consumo, lectura_anterior, lectura_actual


def seleccionar_estado_pago(fecha_vencimiento: date) -> str:
    """Selecciona estado de pago basado en fecha y probabilidades"""
    hoy = date.today()
    
    # Si la fecha de vencimiento no ha llegado, solo puede ser pendiente o pagada
    if fecha_vencimiento > hoy:
        return 'pagada' if random.random() < 0.3 else 'pendiente'
    
    # Si ya venció, puede ser cualquier estado
    rand = random.random()
    acumulado = 0
    
    for estado, probabilidad in ESTADOS_PAGO:
        acumulado += probabilidad
        if rand <= acumulado:
            # Si está vencida, marcar como vencida
            if fecha_vencimiento < hoy and estado == 'pendiente':
                return 'vencida'
            return estado
    
    return 'pagada'


def generar_periodo_facturacion(año: int, mes: int) -> str:
    """Genera el string de período de facturación"""
    return f"{año}-{mes:02d}"


def generar_fechas_boleta(año: int, mes: int) -> tuple:
    """
    Genera las fechas de emisión y vencimiento para una boleta
    
    Returns:
        tuple: (fecha_emision, fecha_vencimiento)
    """
    # Emisión entre el 5 y 8 del mes
    dia_emision = random.randint(5, 8)
    fecha_emision = date(año, mes, dia_emision)
    
    # Vencimiento el 25 del mismo mes
    dia_vencimiento = 25
    fecha_vencimiento = date(año, mes, dia_vencimiento)
    
    return fecha_emision, fecha_vencimiento


# ============================================================================
# FUNCIÓN PRINCIPAL DE POBLACIÓN
# ============================================================================

def poblar_boletas(
    meses_atras: int = 12,
    usuarios: list = None,
    limpiar_existentes: bool = False,
    patron_consumo: str = 'normal',
    variabilidad: bool = True
):
    """
    Puebla la base de datos con boletas simuladas
    
    Args:
        meses_atras: Cantidad de meses hacia atrás a generar
        usuarios: Lista de usuarios a crear boletas (usa USUARIOS_SIMULADOS si es None)
        limpiar_existentes: Si True, elimina boletas existentes antes de crear nuevas
        patron_consumo: Patrón de consumo base ('bajo', 'normal', 'alto', 'muy_alto')
        variabilidad: Si True, añade variabilidad aleatoria entre usuarios
    """
    
    print("\n" + "="*80)
    print(" SCRIPT DE POBLACIÓN DE BOLETAS ".center(80, "="))
    print("="*80 + "\n")
    
    # Limpiar existentes si se solicita
    if limpiar_existentes:
        print("🗑️  Limpiando boletas existentes...")
        count_deleted = Boleta.objects.all().count()
        Boleta.objects.all().delete()
        print(f"   ✅ {count_deleted} boletas eliminadas\n")
    
    # Usar usuarios por defecto si no se especifican
    if usuarios is None:
        usuarios = USUARIOS_SIMULADOS
    
    print(f"👥 Usuarios a procesar: {len(usuarios)}")
    print(f"📅 Períodos a generar: {meses_atras} meses")
    print(f"📊 Patrón de consumo base: {patron_consumo}")
    print(f"🎲 Variabilidad: {'Activada' if variabilidad else 'Desactivada'}\n")
    
    # Contadores
    total_creadas = 0
    total_errores = 0
    
    # Generar boletas para cada usuario
    for usuario in usuarios:
        print(f"\n{'='*80}")
        print(f"👤 Usuario: {usuario['nombre']} ({usuario['rut']})")
        print(f"📍 Dirección: {usuario['direccion']}")
        print(f"{'='*80}\n")
        
        # Determinar patrón de consumo para este usuario
        if variabilidad:
            patrones_disponibles = list(PATRONES_CONSUMO.keys())
            patron_usuario = random.choice(patrones_disponibles)
        else:
            patron_usuario = patron_consumo
        
        print(f"📊 Patrón asignado: {patron_usuario.upper()}")
        
        # Inicializar lectura
        lectura_previa = None
        boletas_usuario = []
        
        # Generar boletas para cada mes
        hoy = date.today()
        
        for i in range(meses_atras, 0, -1):
            # Calcular fecha del período
            fecha_periodo = hoy - timedelta(days=30*i)
            año = fecha_periodo.year
            mes = fecha_periodo.month
            
            try:
                # Generar fechas
                fecha_emision, fecha_vencimiento = generar_fechas_boleta(año, mes)
                
                # Generar consumo
                consumo, lectura_anterior, lectura_actual = generar_consumo_realista(
                    mes, 
                    patron_usuario,
                    lectura_previa
                )
                lectura_previa = lectura_actual
                
                # Calcular monto
                monto = calcular_monto(consumo)
                
                # Seleccionar estado
                estado_pago = seleccionar_estado_pago(fecha_vencimiento)
                
                # Crear boleta
                boleta = Boleta.objects.create(
                    rut=usuario['rut'],
                    nombre=usuario['nombre'],
                    direccion=usuario['direccion'],
                    periodo_facturacion=generar_periodo_facturacion(año, mes),
                    fecha_emision=fecha_emision,
                    fecha_vencimiento=fecha_vencimiento,
                    consumo=consumo,
                    lectura_anterior=lectura_anterior,
                    lectura_actual=lectura_actual,
                    monto=monto,
                    estado_pago=estado_pago
                )
                
                boletas_usuario.append(boleta)
                total_creadas += 1
                
                # Emoji según estado
                estado_emoji = {
                    'pagada': '✅',
                    'pendiente': '⏳',
                    'vencida': '⚠️',
                    'anulada': '❌'
                }
                emoji = estado_emoji.get(estado_pago, '📄')
                
                print(f"   {emoji} {boleta.periodo_facturacion}: "
                      f"{consumo} m³ → ${monto:,.0f} ({estado_pago})")
                
            except Exception as e:
                print(f"   ❌ Error en período {año}-{mes:02d}: {e}")
                total_errores += 1
        
        # Resumen del usuario
        if boletas_usuario:
            consumos = [float(b.consumo) for b in boletas_usuario]
            consumo_promedio = sum(consumos) / len(consumos)
            consumo_min = min(consumos)
            consumo_max = max(consumos)
            
            print(f"\n   📈 Resumen:")
            print(f"      • Boletas creadas: {len(boletas_usuario)}")
            print(f"      • Consumo promedio: {consumo_promedio:.1f} m³")
            print(f"      • Rango: {consumo_min:.1f} - {consumo_max:.1f} m³")
    
    # Resumen final
    print("\n" + "="*80)
    print(" RESUMEN FINAL ".center(80, "="))
    print("="*80 + "\n")
    
    print(f"✅ Total boletas creadas: {total_creadas}")
    print(f"❌ Total errores: {total_errores}")
    print(f"👥 Usuarios procesados: {len(usuarios)}")
    print(f"📊 Boletas por usuario: ~{total_creadas // len(usuarios) if usuarios else 0}")
    
    # Estadísticas por estado
    print("\n📋 Estadísticas por estado de pago:")
    for estado, _ in ESTADOS_PAGO:
        count = Boleta.objects.filter(estado_pago=estado).count()
        porcentaje = (count / total_creadas * 100) if total_creadas > 0 else 0
        print(f"   • {estado.capitalize()}: {count} ({porcentaje:.1f}%)")
    
    # Estadísticas de consumo
    print("\n📊 Estadísticas de consumo:")
    all_boletas = Boleta.objects.all()
    if all_boletas.exists():
        consumos = [float(b.consumo) for b in all_boletas]
        print(f"   • Promedio general: {sum(consumos)/len(consumos):.1f} m³")
        print(f"   • Mínimo: {min(consumos):.1f} m³")
        print(f"   • Máximo: {max(consumos):.1f} m³")
    
    print("\n" + "="*80)
    print("\n✅ Población completada exitosamente!\n")


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def crear_usuario_personalizado(rut: str, nombre: str, direccion: str, meses: int = 12, patron: str = 'normal'):
    """Crea boletas para un usuario personalizado"""
    usuario = {'rut': rut, 'nombre': nombre, 'direccion': direccion}
    poblar_boletas(
        meses_atras=meses,
        usuarios=[usuario],
        limpiar_existentes=False,
        patron_consumo=patron,
        variabilidad=False
    )


def mostrar_estadisticas():
    """Muestra estadísticas actuales de la base de datos"""
    print("\n" + "="*80)
    print(" ESTADÍSTICAS DE BASE DE DATOS ".center(80, "="))
    print("="*80 + "\n")
    
    total = Boleta.objects.count()
    print(f"📊 Total de boletas: {total}")
    
    if total == 0:
        print("\n⚠️  No hay boletas en la base de datos\n")
        return
    
    # Por usuario
    print("\n👥 Boletas por usuario:")
    usuarios = Boleta.objects.values('rut', 'nombre').distinct()
    for usuario in usuarios:
        count = Boleta.objects.filter(rut=usuario['rut']).count()
        print(f"   • {usuario['nombre']} ({usuario['rut']}): {count} boletas")
    
    # Por estado
    print("\n📋 Por estado de pago:")
    for estado, _ in ESTADOS_PAGO:
        count = Boleta.objects.filter(estado_pago=estado).count()
        porcentaje = (count / total * 100) if total > 0 else 0
        print(f"   • {estado.capitalize()}: {count} ({porcentaje:.1f}%)")
    
    # Consumo
    print("\n📊 Estadísticas de consumo:")
    consumos = [float(b.consumo) for b in Boleta.objects.all()]
    if consumos:
        print(f"   • Promedio: {sum(consumos)/len(consumos):.1f} m³")
        print(f"   • Mínimo: {min(consumos):.1f} m³")
        print(f"   • Máximo: {max(consumos):.1f} m³")
    
    print("\n" + "="*80 + "\n")


def limpiar_base_datos():
    """Limpia todas las boletas de la base de datos"""
    print("\n⚠️  ADVERTENCIA: Esta acción eliminará TODAS las boletas de la base de datos")
    confirmacion = input("Escribe 'CONFIRMAR' para continuar: ")
    
    if confirmacion == 'CONFIRMAR':
        count = Boleta.objects.count()
        Boleta.objects.all().delete()
        print(f"\n✅ {count} boletas eliminadas\n")
    else:
        print("\n❌ Operación cancelada\n")


# ============================================================================
# MENÚ INTERACTIVO
# ============================================================================

def menu_principal():
    """Menú interactivo principal"""
    while True:
        print("\n" + "="*80)
        print(" MENÚ PRINCIPAL - POBLACIÓN DE BOLETAS ".center(80, "="))
        print("="*80 + "\n")
        
        print("1. 📝 Poblar con usuarios predefinidos (12 meses)")
        print("2. 🎯 Poblar con patrón personalizado")
        print("3. 👤 Crear usuario personalizado")
        print("4. 📊 Ver estadísticas")
        print("5. 🗑️  Limpiar base de datos")
        print("6. 🚪 Salir")
        
        opcion = input("\nSelecciona una opción (1-6): ").strip()
        
        if opcion == '1':
            poblar_boletas(
                meses_atras=12,
                limpiar_existentes=False,
                variabilidad=True
            )
        
        elif opcion == '2':
            print("\nPatrones disponibles:")
            print("  1. bajo (8-12 m³)")
            print("  2. normal (12-18 m³)")
            print("  3. alto (18-25 m³)")
            print("  4. muy_alto (25-35 m³)")
            
            patron_idx = input("\nSelecciona patrón (1-4): ").strip()
            patrones = ['bajo', 'normal', 'alto', 'muy_alto']
            patron = patrones[int(patron_idx)-1] if patron_idx in ['1','2','3','4'] else 'normal'
            
            meses = input("Cantidad de meses (default 12): ").strip()
            meses = int(meses) if meses.isdigit() else 12
            
            limpiar = input("¿Limpiar boletas existentes? (s/N): ").strip().lower()
            
            poblar_boletas(
                meses_atras=meses,
                patron_consumo=patron,
                limpiar_existentes=(limpiar == 's'),
                variabilidad=False
            )
        
        elif opcion == '3':
            print("\n--- Crear Usuario Personalizado ---")
            rut = input("RUT (formato 12345678-9): ").strip()
            nombre = input("Nombre completo: ").strip()
            direccion = input("Dirección: ").strip()
            
            print("\nPatrones: 1=bajo, 2=normal, 3=alto, 4=muy_alto")
            patron_idx = input("Patrón (1-4, default 2): ").strip()
            patrones = ['bajo', 'normal', 'alto', 'muy_alto']
            patron = patrones[int(patron_idx)-1] if patron_idx in ['1','2','3','4'] else 'normal'
            
            meses = input("Cantidad de meses (default 12): ").strip()
            meses = int(meses) if meses.isdigit() else 12
            
            crear_usuario_personalizado(rut, nombre, direccion, meses, patron)
        
        elif opcion == '4':
            mostrar_estadisticas()
        
        elif opcion == '5':
            limpiar_base_datos()
        
        elif opcion == '6':
            print("\n👋 ¡Hasta luego!\n")
            break
        
        else:
            print("\n❌ Opción inválida\n")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Poblar base de datos con boletas simuladas')
    parser.add_argument('--meses', type=int, default=12, help='Cantidad de meses a generar')
    parser.add_argument('--patron', choices=['bajo', 'normal', 'alto', 'muy_alto'], 
                       default='normal', help='Patrón de consumo')
    parser.add_argument('--limpiar', action='store_true', help='Limpiar boletas existentes')
    parser.add_argument('--stats', action='store_true', help='Solo mostrar estadísticas')
    parser.add_argument('--menu', action='store_true', help='Mostrar menú interactivo')
    
    args = parser.parse_args()
    
    try:
        if args.stats:
            mostrar_estadisticas()
        elif args.menu:
            menu_principal()
        else:
            poblar_boletas(
                meses_atras=args.meses,
                patron_consumo=args.patron,
                limpiar_existentes=args.limpiar,
                variabilidad=True
            )
    except KeyboardInterrupt:
        print("\n\n❌ Operación interrumpida por el usuario\n")
    except Exception as e:
        print(f"\n\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
