# Documentación del Módulo de Emergencias - Chatbot RAG

## 📋 Índice

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Flujo Conversacional](#flujo-conversacional)
4. [Base de Datos](#base-de-datos)
5. [Sistema RAG](#sistema-rag)
6. [API REST](#api-rest)
7. [Instalación y Configuración](#instalación-y-configuración)
8. [Uso y Ejemplos](#uso-y-ejemplos)
9. [Despliegue](#despliegue)

---

## 🎯 Introducción

### Propósito

El Módulo de Emergencias es un chatbot inteligente basado en RAG (Retrieval-Augmented Generation) que permite a los usuarios de la Cooperativa de Agua Potable reportar emergencias relacionadas con el servicio de agua de manera automatizada, guiada y eficiente.

### Características Principales

- ✅ **Conversación Guiada**: El chatbot entrevista al usuario siguiendo un flujo estructurado
- ✅ **Recolección Estructurada**: Recopila 7 datos clave (X1-X7) según diagrama de flujo
- ✅ **RAG Inteligente**: Usa base de conocimiento para respuestas contextualizadas
- ✅ **Cálculo Automático de Prioridad**: Clasifica emergencias en 4 niveles
- ✅ **Integración LLM**: Utiliza Google Gemini para procesamiento de lenguaje natural
- ✅ **Historial Persistente**: Almacena conversaciones y mensajes
- ✅ **API REST Completa**: Endpoints para gestión de emergencias y chat

### Tecnologías Utilizadas

**Backend:**
- Django 5.2.8
- Django REST Framework 3.16.1
- Google Gemini (gemini-pro)
- ChromaDB 0.5.23
- LangChain 0.3.13
- Sentence Transformers

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
│  │              ModuloEmergencia                        │  │
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
│  │  │  - Extracción de datos                     │  │  │
│  │  │  - Cálculo de prioridad                    │  │  │
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
│  │                      │  │ (LangChain)      │  │ │  │
│  │                      │  └──────────────────┘  │ │  │
│  │                      └─────────────────────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Base de Datos                             │
│  - Emergencias                                               │
│  - ChatConversation                                          │
│  - ChatMessage                                               │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principales

#### 1. **Views (API Layer)**
- `EmergenciaViewSet`: CRUD de emergencias
- `ChatConversationViewSet`: Gestión de conversaciones
- `init_chat()`: Iniciar nueva conversación
- `chat_message()`: Procesar mensajes
- `chat_status()`: Consultar estado
- `rag_stats()`: Estadísticas del sistema RAG

#### 2. **ChatbotService**
Servicio principal que implementa la lógica conversacional:
- Manejo de estados del flujo
- Extracción de datos con LLM
- Integración con RAG
- Cálculo de prioridad
- Generación de respuestas contextualizadas

#### 3. **Sistema RAG**
- **VectorStoreManager**: Gestión de ChromaDB
- **DocumentProcessor**: Procesamiento y chunking de documentos
- **RAGRetriever**: Recuperación de información relevante
- **EmbeddingsManager**: Gestión de embeddings

#### 4. **Modelos de Datos**
- **Emergencia**: Registro de emergencias
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
┌────────────────────────┐
│ Chatbot entrevista     │
│ al usuario             │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Chatbot rescata datos: │
│ X1: Sector             │
│ X2: Datos medidor/fuga │
│ X3: Fecha              │
│ X4: Nombre usuario     │
│ X5: Fotografía (opt)   │
│ X6: Dirección          │
│ X7: Teléfono           │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Se calcula nivel de    │
│ gravedad emergencia    │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Se asigna nivel de     │
│ prioridad              │
└────────┬───────────────┘
         │
         ▼
    ┌────────┐
    │¿Usuario│  ──NO──► FIN
    │solicita│
    │contacto│
    │colabo? │
    └────┬───┘
         │ SÍ
         ▼
┌────────────────────────┐
│ Se otorgan contactos   │
│ requeridos             │
└────────┬───────────────┘
         │
         ▼
     ┌─────┐
     │ FIN │
     └─────┘
```

### Estados de la Conversación

1. **`iniciada`**: Conversación creada, mensaje inicial enviado
2. **`recolectando_datos`**: Recolectando X1-X7
3. **`calculando_prioridad`**: Calculando nivel de emergencia
4. **`solicitando_contacto`**: Preguntando por datos de contacto
5. **`finalizada`**: Conversación completada
6. **`abandonada`**: Usuario abandonó (timeout)

### Datos Recolectados (X1-X7)

| Dato | Campo | Descripción | Requerido |
|------|-------|-------------|-----------|
| X1 | `sector` | Sector donde ocurre (7 opciones) | ✅ |
| X2 | `datos_medidor_fuga` | Medidor corriendo, cantidad agua | ✅ |
| X3 | `fecha` | Fecha del reporte | ✅ |
| X4 | `nombre_usuario` | Nombre completo | ✅ |
| X5 | `fotografia` | Foto del problema | ❌ (opcional) |
| X6 | `direccion` | Dirección exacta | ✅ |
| X7 | `telefono` | Teléfono de contacto | ✅ |

---

## 💾 Base de Datos

### Modelo: Emergencia

```python
class Emergencia(models.Model):
    # PK
    id_emergencia = UUIDField(primary_key=True)
    
    # Datos del usuario (X1, X4, X6, X7)
    nombre_usuario = CharField(max_length=200)
    telefono = CharField(max_length=17)
    sector = CharField(choices=SECTORES)
    direccion = CharField(max_length=500)
    
    # Datos de la emergencia (X2, X5)
    descripcion = TextField()
    tipo_emergencia = CharField(choices=TIPOS_EMERGENCIA)
    medidor_corriendo = BooleanField(null=True)
    cantidad_agua = CharField(max_length=200)
    fotografia = ImageField(upload_to='emergencias/fotos/')
    
    # Estado y prioridad
    estado_emergencia = CharField(choices=ESTADOS, default='pendiente')
    nivel_prioridad = CharField(choices=NIVELES_PRIORIDAD)
    
    # Contacto colaborativo
    solicita_contacto_colaborativo = BooleanField(default=False)
    
    # Timestamps
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_actualizacion = DateTimeField(auto_now=True)
    
    # Notas internas
    notas_internas = TextField(blank=True)
```

**Sectores:**
- `anibana`
- `el_molino`
- `la_compania`
- `el_maiten_1`
- `la_morera`
- `el_maiten_2`
- `santa_margarita`

**Tipos de Emergencia:**
- `rotura_matriz`
- `baja_presion`
- `fuga_agua`
- `caneria_rota`
- `agua_contaminada`
- `sin_agua`
- `otro`

**Niveles de Prioridad:**
- `baja`: Consultas generales
- `media`: Fugas moderadas, baja presión
- `alta`: Agua contaminada, cañería rota
- `critica`: Rotura matriz, sin agua

### Modelo: ChatConversation

```python
class ChatConversation(models.Model):
    session_id = CharField(unique=True)
    estado = CharField(choices=ESTADOS_CONVERSACION)
    datos_recolectados = JSONField(default=dict)
    emergencia = OneToOneField(Emergencia, null=True)
    fecha_inicio = DateTimeField(auto_now_add=True)
    fecha_fin = DateTimeField(null=True)
```

### Modelo: ChatMessage

```python
class ChatMessage(models.Model):
    conversation = ForeignKey(ChatConversation)
    rol = CharField(choices=['usuario', 'asistente', 'sistema'])
    contenido = TextField()
    timestamp = DateTimeField(auto_now_add=True)
    metadata = JSONField(default=dict)
```

---

## 🔍 Sistema RAG

### Arquitectura RAG

```
Documentos (.md)
     │
     ▼
┌──────────────────┐
│DocumentProcessor │
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
1. `protocolos_emergencias.md`
   - Tipos de emergencias
   - Procedimientos
   - Prioridades
   - Horarios

2. `sectores_informacion.md`
   - 7 sectores atendidos
   - Características
   - Problemas comunes
   - Perfil de usuarios

3. `contactos_cooperativa.md`
   - Teléfonos (Recaudación, Gerencia, Operadores)
   - Horarios
   - Canales de comunicación
   - Tiempos de respuesta

4. `faq_preguntas_frecuentes.md`
   - Preguntas comunes
   - Sobre la cooperativa
   - Emergencias
   - Facturación
   - Reclamos

### Configuración RAG

```python
RAG_CONFIG = {
    'chunk_size': 1000,              # Tamaño de chunks
    'chunk_overlap': 200,            # Overlap entre chunks
    'top_k_results': 5,              # Top-K documentos a recuperar
    'embedding_model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
}
```

### Ingesta de Documentos

```bash
# Ejecutar script de ingesta
python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py
```

Este script:
1. Procesa todos los `.md` de `knowledge_base/`
2. Los divide en chunks
3. Genera embeddings automáticamente
4. Los almacena en ChromaDB
5. Ejecuta pruebas de recuperación

---

## 🌐 API REST

### Base URL
```
http://localhost:8000/api/emergencias/
```

### Endpoints

#### 1. Iniciar Conversación

**POST** `/api/emergencias/chat/init/`

Request:
```json
{
  "session_id": "optional-uuid"  // Opcional, se genera si no se provee
}
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "¡Hola! Soy el asistente virtual...",
  "estado": "iniciada"
}
```

#### 2. Enviar Mensaje

**POST** `/api/emergencias/chat/message/`

Request:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Tengo una fuga de agua en El Molino"
}
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Entiendo que tienes una fuga en El Molino. ¿Cuál es tu dirección exacta?",
  "estado": "recolectando_datos",
  "completed": false,
  "datos_recolectados": ["sector", "descripcion"],
  "datos_faltantes": ["nombre_usuario", "telefono", "direccion"]
}
```

#### 3. Consultar Estado

**GET** `/api/emergencias/chat/status/{session_id}/`

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "recolectando_datos",
  "datos_recolectados": {
    "sector": "el_molino",
    "descripcion": "Fuga de agua"
  },
  "emergencia_id": null,
  "fecha_inicio": "2025-12-05T10:30:00Z"
}
```

#### 4. Listar Emergencias

**GET** `/api/emergencias/emergencias/`

Query params:
- `?estado=pendiente`
- `?sector=el_molino`
- `?prioridad=alta`
- `?page=1&page_size=20`

Response:
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/emergencias/emergencias/?page=2",
  "previous": null,
  "results": [
    {
      "id_emergencia": "uuid",
      "nombre_usuario": "Juan Pérez",
      "sector": "el_molino",
      "tipo_emergencia": "fuga_agua",
      "nivel_prioridad": "media",
      "estado_emergencia": "pendiente",
      "fecha_creacion": "2025-12-05T10:35:00Z"
    }
  ]
}
```

#### 5. Obtener Emergencia

**GET** `/api/emergencias/emergencias/{id}/`

#### 6. Actualizar Estado de Emergencia

**PATCH** `/api/emergencias/emergencias/{id}/actualizar_estado/`

Request:
```json
{
  "estado": "en_proceso"
}
```

#### 7. Estadísticas

**GET** `/api/emergencias/emergencias/estadisticas/`

Response:
```json
{
  "total": 42,
  "por_estado": [
    {"estado_emergencia": "pendiente", "count": 15},
    {"estado_emergencia": "en_proceso", "count": 10}
  ],
  "por_prioridad": [...],
  "por_sector": [...]
}
```

#### 8. Estadísticas RAG

**GET** `/api/emergencias/rag/stats/`

Response:
```json
{
  "name": "emergencias_knowledge_base",
  "count": 127,
  "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "provider": "ChromaDB"
}
```

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

- Python 3.10+
- pip
- Git

### 2. Clonar Repositorio

```bash
git clone https://github.com/DaniBOD/Chatbot-Backend.git
cd Chatbot-Backend/Backend
```

### 3. Crear Entorno Virtual

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 4. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env y agregar tu API key de Gemini
GEMINI_API_KEY=tu_api_key_aqui
```

**Obtener API Key de Gemini:**
1. Ir a https://makersuite.google.com/app/apikey
2. Crear/copiar API key
3. Pegar en `.env`

### 6. Crear Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crear Superusuario (Opcional)

```bash
python manage.py createsuperuser
```

### 8. Ingestar Documentos al RAG

```bash
python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py
```

Deberías ver:
```
=== Iniciando ingesta de documentos ===
Procesando documentos de: ...
Total de chunks procesados: 127
✅ Documentos ingresados exitosamente
📊 Total de documentos en colección: 127
```

### 9. Iniciar Servidor

```bash
python manage.py runserver
```

El servidor estará disponible en: `http://localhost:8000`

### 10. Verificar Instalación

Visitar: `http://localhost:8000/admin/`
API Root: `http://localhost:8000/api/emergencias/`

---

## 💡 Uso y Ejemplos

### Ejemplo 1: Flujo Completo de Reporte

**1. Iniciar conversación:**
```bash
curl -X POST http://localhost:8000/api/emergencias/chat/init/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

**2. Usuario reporta problema:**
```bash
curl -X POST http://localhost:8000/api/emergencias/chat/message/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "tu-session-id",
    "message": "Hola, tengo una fuga de agua muy grande en mi casa"
  }'
```

**3. Bot solicita sector:**
```bash
curl -X POST http://localhost:8000/api/emergencias/chat/message/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "tu-session-id",
    "message": "Estoy en El Molino"
  }'
```

**4. Continuar hasta completar X1-X7...**

**5. Bot calcula prioridad y pregunta por contacto:**
```json
{
  "message": "✅ Tu emergencia ha sido registrada con prioridad ALTA...",
  "emergencia_id": "uuid",
  "nivel_prioridad": "alta",
  "completed": false
}
```

**6. Usuario responde sobre contacto:**
```bash
curl -X POST http://localhost:8000/api/emergencias/chat/message/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "tu-session-id",
    "message": "Sí, por favor"
  }'
```

**7. Bot entrega contactos y finaliza:**
```json
{
  "message": "📞 Contactos: Recaudación: +56 9 8149 4350...",
  "estado": "finalizada",
  "completed": true
}
```

### Ejemplo 2: Consultar Emergencias

```python
import requests

# Listar emergencias pendientes del sector El Molino
response = requests.get(
    'http://localhost:8000/api/emergencias/emergencias/',
    params={
        'estado': 'pendiente',
        'sector': 'el_molino'
    }
)

emergencias = response.json()['results']
for em in emergencias:
    print(f"ID: {em['id_emergencia']}")
    print(f"Usuario: {em['nombre_usuario']}")
    print(f"Prioridad: {em['nivel_prioridad']}")
    print("---")
```

### Ejemplo 3: Integración desde Frontend (React)

```javascript
// Iniciar conversación
const initChat = async () => {
  const response = await fetch('http://localhost:8000/api/emergencias/chat/init/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  
  const data = await response.json();
  setSessionId(data.session_id);
  setMessages([{ role: 'asistente', content: data.message }]);
};

// Enviar mensaje
const sendMessage = async (userMessage) => {
  const response = await fetch('http://localhost:8000/api/emergencias/chat/message/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message: userMessage
    })
  });
  
  const data = await response.json();
  setMessages(prev => [
    ...prev,
    { role: 'usuario', content: userMessage },
    { role: 'asistente', content: data.message }
  ]);
  
  if (data.completed) {
    setConversationComplete(true);
  }
};
```

---

## 📦 Despliegue

### Producción con PostgreSQL

1. **Instalar PostgreSQL**

2. **Configurar en `.env`:**
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=chatbot_prod
DB_USER=chatbot_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
```

3. **Actualizar `settings.py`:**
```python
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}
```

4. **Migrar:**
```bash
python manage.py migrate
```

### Despliegue con Docker

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

CMD ["gunicorn", "chatbot_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: chatbot_db
      POSTGRES_USER: chatbot_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: gunicorn chatbot_backend.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

**Ejecutar:**
```bash
docker-compose up --build
```

### Consideraciones de Producción

1. **Seguridad:**
   - Cambiar `SECRET_KEY` en producción
   - `DEBUG = False`
   - Configurar `ALLOWED_HOSTS`
   - Usar HTTPS
   - Proteger API con autenticación

2. **Performance:**
   - Usar PostgreSQL
   - Configurar cache (Redis)
   - Nginx como reverse proxy
   - Limitar tasa de peticiones

3. **Monitoreo:**
   - Logging estructurado
   - Métricas de uso de API
   - Monitoreo de errores (Sentry)
   - Alertas para emergencias críticas

4. **Backup:**
   - Backup diario de base de datos
   - Backup de ChromaDB
   - Backup de archivos media

---

## 📚 Referencias

- **Django**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Google Gemini**: https://ai.google.dev/docs
- **LangChain**: https://python.langchain.com/docs/
- **ChromaDB**: https://docs.trychroma.com/
- **Sentence Transformers**: https://www.sbert.net/

---

## 👥 Contacto y Soporte

**Proyecto:** Chatbot Backend - Módulo de Emergencias
**Repositorio:** https://github.com/DaniBOD/Chatbot-Backend
**Cooperativa:** laciacoop@gmail.com

---

## 📝 Notas Finales

### Trabajo Futuro

- [ ] Implementar WebSockets para chat en tiempo real
- [ ] Agregar autenticación JWT
- [ ] Soporte para carga de fotos en chat
- [ ] Notificaciones push a operadores
- [ ] Dashboard de métricas
- [ ] Tests automatizados
- [ ] Integración con Gemini Vision API para análisis de fotos
- [ ] Módulo de Boletas (pendiente)

### Changelog

**v1.0.0** (2025-12-05)
- ✅ Implementación completa del módulo de emergencias
- ✅ Sistema RAG con ChromaDB
- ✅ Integración con Google Gemini
- ✅ API REST completa
- ✅ Base de conocimiento inicial
- ✅ Flujo conversacional según diagrama
- ✅ Cálculo automático de prioridad

---

**Última actualización:** 5 de diciembre de 2025