# Documentación del Módulo de Boletas - Chatbot RAG

## 📋 Índice

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Flujo Conversacional](#flujo-conversacional)
4. [Base de Datos](#base-de-datos)
5. [Sistema RAG](#sistema-rag)
6. [API REST](#api-rest)
7. [Instalación y Configuración](#instalación-y-configuración)
8. [Uso y Ejemplos](#uso-y-ejemplos)
9. [Tests](#tests)

---

## 🎯 Introducción

### Propósito

El Módulo de Boletas es un chatbot inteligente basado en RAG (Retrieval-Augmented Generation) que permite a los usuarios de la Cooperativa de Agua Potable consultar información sobre sus boletas de consumo de manera automatizada, guiada y eficiente.

### Características Principales

- ✅ **Conversación Guiada**: El chatbot entrevista al usuario siguiendo un flujo estructurado
- ✅ **Consultas Personalizadas**: Rescata datos específicos de boletas del usuario
- ✅ **RAG Inteligente**: Usa base de conocimiento para respuestas contextualizadas sobre tarifas, consumos y FAQ
- ✅ **Consultas Comparativas**: Compara consumos entre diferentes períodos
- ✅ **Integración LLM**: Utiliza Google Gemini para procesamiento de lenguaje natural
- ✅ **Historial Persistente**: Almacena conversaciones y mensajes
- ✅ **API REST Completa**: Endpoints para gestión de boletas y chat
- ✅ **Validación RUT**: Validación automática de RUT chileno

### Tecnologías Utilizadas

**Backend:**
- Django 5.2.8
- Django REST Framework 3.16.1
- Google Gemini (gemini-2.5-flash)
- ChromaDB 1.3.5
- LangChain 0.3.27
- Sentence Transformers 5.1.2

**Base de Datos:**
- SQLite (desarrollo)
- PostgreSQL (producción recomendado)

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                        USUARIO                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                    HTTP/REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Django Backend                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ModuloBoletas                           │  │
│  │                                                      │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────┐ │  │
│  │  │   Views     │  │  Serializers │  │   Models  │ │  │
│  │  │  (API REST) │◄─┤   (DRF)     │◄─┤ (Django)  │ │  │
│  │  └──────┬──────┘  └──────────────┘  └───────────┘ │  │
│  │         │                                          │  │
│  │         ▼                                          │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │      ChatbotService                         │  │  │
│  │  │  - Lógica conversacional                   │  │  │
│  │  │  - Extracción de datos (RUT, período)      │  │  │
│  │  │  - Rescate de datos de boletas            │  │  │
│  │  │  - Consultas comparativas                  │  │  │
│  │  └──────────────┬──────────────────────────────┘  │  │
│  │                 │                                  │  │
│  │     ┌───────────┴───────────┐                     │  │
│  │     ▼                       ▼                     │  │
│  │  ┌────────────┐      ┌─────────────────────────┐ │  │
│  │  │   Gemini   │      │     RAG System          │ │  │
│  │  │    LLM     │      │  ┌──────────────────┐  │ │  │
│  │  │ (API Call) │      │  │  RAGRetriever    │  │ │  │
│  │  └────────────┘      │  │  - Query docs    │  │ │  │
│  │                      │  └────────┬─────────┘  │ │  │
│  │                      │           │            │ │  │
│  │                      │  ┌────────▼─────────┐  │ │  │
│  │                      │  │  VectorStore     │  │ │  │
│  │                      │  │  (ChromaDB)      │  │ │  │
│  │                      │  └──────────────────┘  │ │  │
│  │                      │           │            │ │  │
│  │                      │  ┌────────▼─────────┐  │ │  │
│  │                      │  │ DocumentProcessor│  │ │  │
│  │                      │  │ (Unstructured)   │  │ │  │
│  │                      │  └──────────────────┘  │ │  │
│  │                      └─────────────────────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Base de Datos                             │
│  - Boletas                                                   │
│  - ChatConversation                                          │
│  - ChatMessage                                               │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principales

#### 1. **Views (API Layer)**
- `BoletaViewSet`: CRUD de boletas
- `ChatConversationViewSet`: Gestión de conversaciones
- `init_chat()`: Iniciar nueva conversación
- `chat_message()`: Procesar mensajes
- `chat_status()`: Consultar estado
- `rag_stats()`: Estadísticas del sistema RAG

#### 2. **ChatbotService**
Servicio principal que implementa la lógica conversacional:
- Manejo de estados del flujo
- Extracción de datos del usuario (RUT, motivo de consulta)
- Verificación de existencia de boletas
- Rescate y presentación de datos de boletas
- Consultas comparativas entre períodos
- Integración con RAG para respuestas contextualizadas

#### 3. **Sistema RAG**
- **VectorStoreManager**: Gestión de ChromaDB
- **DocumentIngester**: Procesamiento y chunking de documentos
- **RAGRetriever**: Recuperación de información relevante
- **EmbeddingsManager**: Gestión de embeddings

#### 4. **Modelos de Datos**
- **Boleta**: Registro de boletas de consumo
- **ChatConversation**: Conversaciones activas
- **ChatMessage**: Mensajes individuales

---

## 🔄 Flujo Conversacional

### Diagrama de Flujo (Implementado)

```
                    ┌─────────┐
                    │ Inicio  │
                    └────┬────┘
                         │
                         ▼
                ┌─────────────────────┐
                │ Iniciar             │
                │ Conversación        │
                └────┬────────────────┘
                     │
                     ▼
                ┌────────────────────┐
                │ Preguntar motivo   │
                │ de consulta        │
                └────┬───────────────┘
                     │
                     ▼
           ┌──────────────────────┐
           │ ¿Cliente tiene       │
           │ boleta en sistema?   │
           └───┬──────────┬───────┘
               │          │
              NO         SÍ
               │          │
               ▼          ▼
        ┌─────────┐  ┌───────────────────┐
        │Solicitar│  │ Rescatar datos    │
        │imagen de│  │ de la boleta      │
        │ boleta  │  │                   │
        └────┬────┘  │ - id_boleta       │
             │       │ - fecha_emision   │
             │       │ - nombre          │
             │       │ - rut             │
             │       │ - direccion       │
             │       │ - monto           │
             │       │ - consumo         │
             │       └────┬──────────────┘
             │            │
             │            ▼
             │       ┌───────────────────┐
             │       │ Enviar Respuesta  │
             │       │ acorde a pregunta │
             │       └────┬──────────────┘
             │            │
             │            ▼
             │       ┌───────────────────┐
             │       │ ¿Consulta es      │
             │       │  comparativa?     │
             │       └───┬──────────┬────┘
             │           │          │
             │          NO         SÍ
             │           │          │
             │           │          ▼
             │           │     ┌───────────────────┐
             │           │     │ Enviar Respuesta  │
             │           │     │ acorde a pregunta │
             │           │     └────┬──────────────┘
             │           │          │
             ▼           ▼          ▼
        ┌────────────────────────────┐
        │           Fin              │
        └────────────────────────────┘
```

### Datos de Boleta (List)

Según el diagrama, los datos que se rescatan de la boleta son:

- **`id_boleta`**: Identificador único de la boleta
- **`fecha_emision`**: Fecha de emisión
- **`nombre`**: Nombre del cliente
- **`rut`**: RUT del cliente  
- **`direccion`**: Dirección del domicilio
- **`monto`**: Monto total a pagar
- **`consumo`**: Consumo en m³

### Estados de la Conversación

1. **`iniciada`**: Conversación creada (transitorio, cambia inmediatamente a recolectando_datos)
2. **`recolectando_datos`**: Recolectando información del usuario (motivo, RUT)
3. **`consultando`**: Procesando consulta sobre boleta
4. **`finalizada`**: Conversación completada

### Datos Recolectados

| Dato | Campo | Descripción | Requerido |
|------|-------|-------------|-----------|
| - | `motivo_consulta` | Razón de la consulta | ✅ |
| - | `rut` | RUT del cliente | ✅ |
| - | `periodo` | Período de facturación (opcional) | ❌ |
| - | `tipo_consulta` | ver_boleta, consultar_monto, revisar_consumo, comparar_periodos | ✅ |

---

## 💾 Base de Datos

### Modelo: Boleta

```python
class Boleta(models.Model):
    # PK
    id_boleta = UUIDField(primary_key=True)
    
    # Datos del cliente
    nombre = CharField(max_length=200)
    rut = CharField(max_length=12, validators=[validar_rut_chileno])
    direccion = CharField(max_length=500)
    
    # Datos de facturación
    fecha_emision = DateField(db_index=True)
    periodo_facturacion = CharField(max_length=20)  # ej: "2024-12"
    consumo = DecimalField(max_digits=10, decimal_places=2)  # m³
    monto = DecimalField(max_digits=10, decimal_places=2)  # CLP
    
    # Lecturas del medidor
    lectura_anterior = DecimalField(max_digits=10, decimal_places=2)
    lectura_actual = DecimalField(max_digits=10, decimal_places=2)
    
    # Fechas y estado
    fecha_vencimiento = DateField(null=True, blank=True)
    estado_pago = CharField(choices=ESTADOS_PAGO, default='pendiente')
    
    # Opcional
    imagen_boleta = ImageField(upload_to='boletas/imagenes/', null=True)
    notas = TextField(blank=True)
    
    # Timestamps
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_actualizacion = DateTimeField(auto_now=True)
    
    # Índices y constraints
    class Meta:
        unique_together = [['rut', 'periodo_facturacion']]
        indexes = [
            Index(fields=['-fecha_emision']),
            Index(fields=['rut']),
            Index(fields=['estado_pago']),
            Index(fields=['periodo_facturacion']),
        ]
```

**Estados de Pago:**
- `pendiente`: Boleta sin pagar
- `pagada`: Boleta pagada
- `vencida`: Boleta con fecha de vencimiento pasada
- `anulada`: Boleta anulada

**Métodos útiles:**
- `calcular_consumo()`: Calcula consumo = lectura_actual - lectura_anterior
- `get_consumo_promedio_diario()`: Consumo promedio por día (consumo / 30)
- `esta_vencida()`: Verifica si fecha_vencimiento < hoy

### Modelo: ChatConversation

```python
class ChatConversation(models.Model):
    session_id = CharField(unique=True)
    estado = CharField(choices=ESTADOS_CONVERSACION)
    datos_recolectados = JSONField(default=dict)
    
    # Relación con boletas
    boleta_principal = ForeignKey(Boleta, null=True, related_name='conversaciones')
    boletas_comparadas = ManyToManyField(Boleta, blank=True)
    es_consulta_comparativa = BooleanField(default=False)
    
    # Timestamps
    fecha_inicio = DateTimeField(auto_now_add=True)
    fecha_fin = DateTimeField(null=True, blank=True)
    
    # Metadata adicional
    metadata = JSONField(default=dict, blank=True)
```

**Estructura de `datos_recolectados`:**
```json
{
  "motivo_consulta": "consultar_monto",
  "rut": "12345678-9",
  "tipo_consulta": "consultar_monto",
  "periodo": "2024-12",
  "periodos_comparar": ["2024-11", "2024-12"]
}
```

### Modelo: ChatMessage

```python
class ChatMessage(models.Model):
    conversation = ForeignKey(ChatConversation, related_name='mensajes')
    rol = CharField(choices=['usuario', 'asistente', 'sistema'])
    contenido = TextField()
    timestamp = DateTimeField(auto_now_add=True, db_index=True)
    metadata = JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['timestamp']
```

---

## 🔍 Sistema RAG

### Arquitectura RAG

```
Documentos (.md)
     │
     ▼
┌──────────────────┐
│DocumentIngester  │
│ - Load docs      │
│ - Split chunks   │
│ - Add metadata   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Embeddings      │
│ (sentence-       │
│  transformers)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   ChromaDB       │
│ (Vector Store)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  RAGRetriever    │
│ - Query          │
│ - Retrieve top-k │
│ - Format context │
└──────────────────┘
```

### Base de Conocimiento

**Documentos incluidos:**

1. **`guia_boletas.md`**
   - Cómo leer una boleta
   - Componentes del cobro
   - Interpretación de lecturas
   - Medidor y su funcionamiento
   - Consumo promedio

2. **`tarifas.md`**
   - Tarifa por m³
   - Cargo fijo mensual
   - Recargos por mora
   - Exenciones y descuentos
   - Ejemplos de cálculo

3. **`preguntas_frecuentes.md`**
   - Preguntas sobre boletas
   - Métodos de pago
   - Plazos de vencimiento
   - Consultas sobre consumo alto
   - Reclamos

### Configuración RAG

```python
RAG_CONFIG = {
    'chunk_size': 800,               # Tamaño de chunks
    'chunk_overlap': 200,            # Overlap entre chunks
    'top_k_results': 3,              # Top-K documentos a recuperar
    'embedding_model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    'collection_name': 'boletas_knowledge_base'
}
```

### Ingesta de Documentos

```bash
# Ejecutar comando de management
python manage.py ingest_knowledge_base

# Con opciones
python manage.py ingest_knowledge_base --reset     # Resetear colección
python manage.py ingest_knowledge_base --stats     # Ver estadísticas
python manage.py ingest_knowledge_base --verbose   # Output detallado
```

Este comando:
1. Procesa todos los `.md` de `RAG/knowledge_base/`
2. Los divide en chunks
3. Genera embeddings automáticamente
4. Los almacena en ChromaDB
5. Reporta estadísticas

**Resultado esperado:**
- 3 archivos procesados
- ~13 chunks generados
- Colección `boletas_knowledge_base` activa

---

## 🌐 API REST

### Base URL
```
/api/boletas/
```

### Endpoints Principales

#### 1. Gestión de Boletas

##### Listar boletas
```http
GET /api/boletas/boletas/
```

**Parámetros de filtrado:**
- `estado_pago`: Filtrar por estado (pendiente, pagada, vencida, anulada)
- `rut`: Filtrar por RUT del cliente
- `periodo`: Filtrar por período (formato: YYYY-MM)
- `fecha_desde`, `fecha_hasta`: Rango de fechas
- `vencidas`: true/false para solo vencidas

**Respuesta:**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/boletas/boletas/?page=2",
  "previous": null,
  "results": [
    {
      "id_boleta": "uuid",
      "nombre": "Juan Pérez",
      "rut": "12345678-9",
      "periodo_facturacion": "2024-12",
      "monto": "25000.00",
      "consumo": "15.50",
      "estado_pago": "pendiente",
      "estado_pago_display": "Pendiente",
      "fecha_emision": "2024-12-01",
      "fecha_vencimiento": "2024-12-25"
    }
  ]
}
```

##### Obtener boleta específica
```http
GET /api/boletas/boletas/{id_boleta}/
```

##### Crear boleta
```http
POST /api/boletas/boletas/
Content-Type: application/json

{
  "nombre": "Juan Pérez",
  "rut": "12345678-9",
  "direccion": "Calle Principal 123",
  "fecha_emision": "2024-12-01",
  "periodo_facturacion": "2024-12",
  "consumo": "15.50",
  "monto": "25000.00",
  "lectura_anterior": "100.0",
  "lectura_actual": "115.5",
  "fecha_vencimiento": "2024-12-25",
  "estado_pago": "pendiente"
}
```

##### Actualizar boleta
```http
PUT /api/boletas/boletas/{id_boleta}/
PATCH /api/boletas/boletas/{id_boleta}/
```

##### Eliminar boleta
```http
DELETE /api/boletas/boletas/{id_boleta}/
```

##### Consultar boletas con criterios múltiples
```http
POST /api/boletas/boletas/consultar/
Content-Type: application/json

{
  "rut": "12345678-9",
  "periodo": "2024-12",
  "fecha_inicio": "2024-01-01",
  "fecha_fin": "2024-12-31"
}
```

##### Calcular consumo de una boleta
```http
GET /api/boletas/boletas/{id_boleta}/calcular_consumo/
```

#### 2. Chat Endpoints

##### Iniciar conversación
```http
POST /api/boletas/chat/init/
Content-Type: application/json

{}
```

**Respuesta:**
```json
{
  "session_id": "uuid-generado",
  "message": "¡Hola! Soy tu asistente virtual...",
  "estado": "recolectando_datos"
}
```

##### Enviar mensaje
```http
POST /api/boletas/chat/message/
Content-Type: application/json

{
  "session_id": "uuid",
  "message": "Quiero ver mi boleta, mi RUT es 12345678-9"
}
```

**Respuesta:**
```json
{
  "message": "Encontré tu boleta del período 2024-12...",
  "estado": "consultando",
  "session_id": "uuid",
  "completed": false,
  "boleta_id": "uuid-boleta",
  "boleta_data": {
    "periodo": "2024-12",
    "monto": "25000.00",
    "consumo": "15.50"
  }
}
```

##### Consultar estado
```http
GET /api/boletas/chat/status/{session_id}/
```

**Respuesta:**
```json
{
  "id": 1,
  "session_id": "uuid",
  "estado": "consultando",
  "datos_recolectados": {
    "motivo_consulta": "consultar_monto",
    "rut": "12345678-9"
  },
  "boleta_principal_id": "uuid",
  "es_consulta_comparativa": false,
  "fecha_inicio": "2024-12-06T10:30:00Z",
  "fecha_fin": null
}
```

##### Estadísticas RAG
```http
GET /api/boletas/rag/stats/
```

**Respuesta:**
```json
{
  "collection_name": "boletas_knowledge_base",
  "document_count": 13,
  "status": "active"
}
```

---

## ⚙️ Instalación y Configuración

### 1. Requisitos Previos

```bash
Python 3.13+
Django 5.2.8+
PostgreSQL 13+ (producción)
```

### 2. Variables de Entorno

Crear archivo `.env`:

```bash
# Django
SECRET_KEY=tu-secret-key-super-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (producción)
DATABASE_URL=postgresql://user:pass@localhost:5432/chatbot_db

# Google Gemini
GOOGLE_API_KEY=tu-api-key-de-gemini

# ChromaDB
CHROMA_DB_PATH=./chroma_db

# RAG Configuration
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=3
```

### 3. Instalación

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd Chatbot-Backend

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Ingestar documentos RAG
python manage.py ingest_knowledge_base

# 7. Crear superusuario (opcional)
python manage.py createsuperuser

# 8. Ejecutar servidor
python manage.py runserver
```

### 4. Verificación

```bash
# Test de conectividad API
curl http://localhost:8000/api/boletas/boletas/

# Test de RAG
curl http://localhost:8000/api/boletas/rag/stats/

# Test de chat
curl -X POST http://localhost:8000/api/boletas/chat/init/
```

---

## 📝 Uso y Ejemplos

### Flujo Completo de Conversación

#### 1. Iniciar conversación
```bash
POST /api/boletas/chat/init/

Response:
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "¡Hola! Soy tu asistente virtual para consultas sobre boletas...",
  "estado": "recolectando_datos"
}
```

#### 2. Usuario proporciona RUT y motivo
```bash
POST /api/boletas/chat/message/
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Quiero saber cuánto debo pagar, mi RUT es 12345678-9"
}

Response:
{
  "message": "Encontré tu boleta del período 2024-12:\n\n📄 Boleta del período: 2024-12\n💰 Monto a pagar: $25,000\n📊 Consumo: 15.5 m³\n📅 Fecha de vencimiento: 25/12/2024\n✅ Estado: Pendiente",
  "estado": "consultando",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "completed": false,
  "boleta_id": "uuid-de-la-boleta",
  "boleta_data": {
    "periodo": "2024-12",
    "monto": "25000.00",
    "consumo": "15.50",
    "estado_pago": "pendiente"
  }
}
```

#### 3. Consulta comparativa
```bash
POST /api/boletas/chat/message/
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "¿Cómo se compara con el mes anterior?"
}

Response:
{
  "message": "Comparación de consumo:\n\n📊 Noviembre 2024: 12.3 m³ - $20,000\n📊 Diciembre 2024: 15.5 m³ - $25,000\n\n📈 Aumento: 3.2 m³ (+26%)\n💸 Diferencia: $5,000\n\nEl aumento puede deberse a...",
  "estado": "finalizada",
  "completed": true,
  "es_consulta_comparativa": true
}
```

### Ejemplos de Consultas Comunes

#### Ver estado de pago
```
Usuario: "¿Está pagada mi boleta? RUT 12345678-9"
Bot: "Tu boleta del período 2024-12 está pendiente de pago..."
```

#### Consultar consumo
```
Usuario: "¿Cuánto consumí este mes?"
Bot: "Tu consumo del período 2024-12 fue de 15.5 m³..."
```

#### Revisar tarifas
```
Usuario: "¿Cuánto cuesta el m³ de agua?"
Bot: "La tarifa actual es de $1,200 por m³..."
```

### Integración con Frontend

```javascript
// Iniciar chat
const initChat = async () => {
  const response = await fetch('/api/boletas/chat/init/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  const data = await response.json();
  return data.session_id;
};

// Enviar mensaje
const sendMessage = async (sessionId, message) => {
  const response = await fetch('/api/boletas/chat/message/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message: message
    })
  });
  return await response.json();
};

// Uso
const sessionId = await initChat();
const response = await sendMessage(sessionId, "Quiero ver mi boleta, RUT 12345678-9");
console.log(response.message);
```

---

## 🧪 Tests

### Cobertura de Tests

El módulo cuenta con **35 tests unitarios**, todos pasando exitosamente ✅.

**Cobertura Real Medida: 61%** (1362 líneas de código, 530 sin cubrir)

#### Desglose de Cobertura por Archivo

| Archivo | Cobertura | Líneas | Sin Cubrir | Estado |
|---------|-----------|--------|------------|--------|
| `tests.py` | **99%** | 275 | 1 | ✅ Excelente |
| `__init__.py` | **100%** | 5 | 0 | ✅ Excelente |
| `apps.py` | **100%** | 5 | 0 | ✅ Excelente |
| `urls.py` | **100%** | 7 | 0 | ✅ Excelente |
| `models.py` | **89%** | 83 | 9 | ✅ Muy Bueno |
| `serializers.py` | **89%** | 75 | 8 | ✅ Muy Bueno |
| `retriever.py` | **63%** | 82 | 30 | ⚠️ Mejorable |
| `admin.py` | **58%** | 137 | 58 | ⚠️ Mejorable |
| `vector_store.py` | **57%** | 63 | 27 | ⚠️ Mejorable |
| `views.py` | **55%** | 189 | 85 | ⚠️ Mejorable |
| `chatbot_service.py` | **44%** | 237 | 133 | ⚠️ Crítico |
| `embeddings.py` | **31%** | 80 | 55 | ❌ Crítico |
| `ingest_documents.py` | **0%** | 67 | 67 | ❌ Sin tests |
| `ingest_knowledge_base.py` | **0%** | 57 | 57 | ❌ Sin tests |

#### Tests por Categoría

**BoletaModelTests (10 tests)** ✅
- Creación y validación de boletas
- Validación de RUT chileno
- Cálculo de consumo promedio diario
- Verificación de vencimiento
- Estados de pago
- Representación en string

**ChatConversationModelTests (3 tests)**
- Creación de conversaciones
- Almacenamiento de datos recolectados
- Estados válidos

**ChatMessageModelTests (4 tests)**
- Mensajes de usuario y asistente
- Representación en string
- Ordenamiento por timestamp

**ChatbotServiceTests (3 tests)**
- Inicio de conversación con mensaje inicial
- Procesamiento de mensajes con contexto
- Mensaje inicial contiene información correcta

**ChatAPITests (7 tests)** ✅
- Inicialización de chat (crea conversación en BD)
- Envío de mensajes exitosos
- Consulta de estado de conversación
- Historial de mensajes
- Manejo de errores (session_id inválido, sin session_id, sin contenido)

**BoletaViewSetTests (6 tests)**
- Listado de boletas
- Filtrado por RUT, estado de pago
- Retrieve de boleta específica
- Endpoint `por_periodo` (filtrar por período)
- Endpoint `vencidas` (boletas vencidas)

**IntegrationTests (2 tests)**
- Flujo completo de consulta de monto
- Endpoint de estadísticas RAG

### Áreas con Cobertura Completa
- ✅ Modelos de base de datos (89%)
- ✅ Serializers DRF (89%)
- ✅ Configuración y URLs (100%)
- ✅ Tests mismos (99%)

### Áreas que Requieren Más Tests
- ⚠️ **chatbot_service.py (44%)** - Lógica conversacional compleja sin tests completos
- ⚠️ **views.py (55%)** - Endpoints custom y acciones sin tests
- ⚠️ **admin.py (58%)** - Acciones personalizadas sin tests
- ⚠️ **Sistema RAG (31-63%)** - Embeddings, vector store, retriever requieren más cobertura
- ❌ **Management commands (0%)** - Sin tests de ingesta
- ❌ **Script de ingesta (0%)** - Procesamiento de documentos sin tests

### Ejecutar Tests

```bash
# Todos los tests (35 tests)
python manage.py test ModuloBoletas

# Con verbosidad
python manage.py test ModuloBoletas --verbosity=2

# Tests específicos por categoría
python manage.py test ModuloBoletas.tests.BoletaModelTests
python manage.py test ModuloBoletas.tests.ChatAPITests
python manage.py test ModuloBoletas.tests.IntegrationTests

# Con análisis de cobertura (requiere coverage instalado)
python -m coverage run --source=ModuloBoletas manage.py test ModuloBoletas
python -m coverage report -m
python -m coverage html  # Genera reporte HTML en htmlcov/
```

### Resultado Esperado

```
Found 35 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...................................
----------------------------------------------------------------------
Ran 35 tests in 3.270s

OK
Destroying test database for alias 'default'...
```

**✅ Todos los 35 tests pasan exitosamente**

### Análisis de Cobertura

Para obtener el reporte de cobertura detallado:

```bash
# Instalar coverage si no está instalado
pip install coverage pytest-cov

# Ejecutar tests con cobertura
python -m coverage run --source=ModuloBoletas manage.py test ModuloBoletas

# Ver reporte en terminal
python -m coverage report -m

# Generar reporte HTML
python -m coverage html
# Abrir htmlcov/index.html en navegador
```

**Reporte de Cobertura:**
```
Name                                                         Stmts   Miss  Cover
--------------------------------------------------------------------------------
ModuloBoletas\models.py                                         83      9    89%
ModuloBoletas\serializers.py                                    75      8    89%
ModuloBoletas\tests.py                                         275      1    99%
ModuloBoletas\views.py                                         189     85    55%
ModuloBoletas\admin.py                                         137     58    58%
ModuloBoletas\services\chatbot_service.py                      237    133    44%
ModuloBoletas\RAG\retriever.py                                  82     30    63%
ModuloBoletas\RAG\vector_store.py                               63     27    57%
ModuloBoletas\RAG\embeddings.py                                 80     55    31%
ModuloBoletas\RAG\ingest_documents.py                           67     67     0%
ModuloBoletas\management\commands\ingest_knowledge_base.py      57     57     0%
--------------------------------------------------------------------------------
TOTAL                                                         1362    530    61%
```

### Estado del Módulo

**Estado General:** ✅ **FUNCIONAL** - Todos los tests pasando

**Recomendaciones:**
- ⚠️ Aumentar cobertura de `chatbot_service.py` (actualmente 44%)
- ⚠️ Agregar tests para management commands (actualmente 0%)
- ⚠️ Mejorar cobertura del sistema RAG (31-63%)
- ⚠️ Testear endpoints avanzados y acciones de admin

**Target recomendado:** 75-80% de cobertura antes de producción

---

## 📚 Referencias Adicionales

### Documentos Relacionados

- [ENDPOINTS.md](../ModuloBoletas/ENDPOINTS.md) - Documentación detallada de todos los endpoints (deprecado, migrado aquí)
- [PLAN_DESARROLLO.md](../ModuloBoletas/PLAN_DESARROLLO.md) - Plan de desarrollo original (deprecado, completado)
- [INSTALACION.md](./INSTALACION.md) - Guía de instalación general del proyecto
- [INICIO_RAPIDO.md](./INICIO_RAPIDO.md) - Guía de inicio rápido
- [DEPENDENCIAS.md](./DEPENDENCIAS.md) - Documentación de dependencias del proyecto

### Estructura de Archivos

```
ModuloBoletas/
├── __init__.py
├── apps.py                     # Configuración de la app
├── models.py                   # Modelos Boleta, ChatConversation, ChatMessage
├── serializers.py              # 10 serializers DRF
├── views.py                    # ViewSets y endpoints de chat
├── urls.py                     # Configuración de URLs
├── admin.py                    # Admin de Django
├── tests.py                    # 35 tests unitarios
├── services/
│   ├── __init__.py
│   └── chatbot_service.py      # Lógica conversacional (~760 líneas)
├── RAG/
│   ├── __init__.py
│   ├── vector_store.py         # ChromaDB manager
│   ├── embeddings.py           # Embeddings manager
│   ├── retriever.py            # RAG retriever
│   ├── ingest_documents.py     # Document processor
│   └── knowledge_base/
│       ├── guia_boletas.md
│       ├── tarifas.md
│       └── preguntas_frecuentes.md
└── management/
    └── commands/
        └── ingest_knowledge_base.py  # Management command
```

### Próximos Pasos

1. ✅ Aplicar migraciones: `python manage.py migrate`
2. ⚠️ Aumentar cobertura de tests (target: 75-80%)
3. ⚠️ Agregar tests para chatbot_service.py y RAG
4. ✅ Configurar frontend
5. ✅ Configurar SSL en producción
6. ✅ Monitoreo y logging

---

## 🤝 Contribuciones

Para contribuir al módulo:

1. Seguir la estructura existente
2. Mantener cobertura de tests >75% (objetivo: 90%)
3. Documentar todos los cambios
4. Actualizar este documento si es necesario
5. Ejecutar tests antes de commit: `python manage.py test ModuloBoletas`
6. Verificar cobertura: `python -m coverage run --source=ModuloBoletas manage.py test ModuloBoletas`

---

## 📄 Licencia

Este proyecto es parte de la Cooperativa de Agua Potable y es de uso interno.

---

**Última actualización:** 6 de Diciembre, 2025  
**Versión:** 1.0.0  
**Autor:** Equipo de Desarrollo Chatbot  
**Estado:** ✅ Funcional - 35/35 tests pasando - Cobertura: 61%
