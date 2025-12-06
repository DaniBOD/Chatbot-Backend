# Contexto del Proyecto: Chatbot Backend - Módulo de Emergencias

## 🎯 Visión General del Proyecto

**Proyecto**: Sistema de Chatbot Inteligente para Cooperativa de Agua Potable  
**Módulo**: Emergencias (Backend)  
**Propósito**: Automatizar el reporte y gestión de emergencias relacionadas con el servicio de agua mediante un chatbot conversacional con RAG  
**Estado**: Prototipo funcional (4 desarrolladores: 2 backend, 2 frontend)  
**Tecnología Principal**: Django 5.2.8 + Google Gemini 2.5 Flash + ChromaDB + LangChain

---

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico

**Backend Framework**
- Django 5.2.8 - Framework web principal
- Django REST Framework 3.16.1 - API REST
- Python 3.11+ - Lenguaje base

**Inteligencia Artificial**
- Google Gemini 2.5 Flash - Modelo LLM para procesamiento de lenguaje natural
- LangChain 0.3.13 - Framework para aplicaciones LLM
- Sentence Transformers 3.3.1 - Embeddings multilingües

**Sistema RAG (Retrieval-Augmented Generation)**
- ChromaDB 0.5.23 - Base de datos vectorial para búsqueda semántica
- Embeddings: paraphrase-multilingual-MiniLM-L12-v2
- Documents: Markdown files con información de la cooperativa

**Base de Datos**
- SQLite (desarrollo/prototipo)
- PostgreSQL (recomendado para producción)

**Frontend (Separado)**
- Vite + React
- Puerto: 5173 (desarrollo)
- Comunicación: API REST con backend en puerto 8000

---

## 📊 Estructura del Proyecto

```
Backend/
├── manage.py                    # Django CLI
├── requirements.txt             # Dependencias Python (25 paquetes)
├── .env                         # Variables de entorno (API keys)
├── .env.example                 # Template de configuración
├── db.sqlite3                   # Base de datos SQLite
├── chroma_db/                   # ChromaDB persistent storage
│
├── chatbot_backend/             # Configuración Django
│   ├── settings.py              # Settings con RAG_CONFIG y Gemini
│   ├── urls.py                  # URLs principales
│   └── wsgi.py/asgi.py          # Deployment
│
├── ModuloEmergencia/            # 🔥 Módulo Principal
│   ├── models.py                # 3 modelos: Emergencia, ChatConversation, ChatMessage
│   ├── views.py                 # ViewSets y endpoints de chat
│   ├── serializers.py           # DRF serializers
│   ├── urls.py                  # URLs del módulo
│   ├── admin.py                 # Admin panel
│   ├── tests.py                 # Tests unitarios (25 tests)
│   │
│   ├── services/                # Lógica de negocio
│   │   └── chatbot_service.py   # 534 líneas - Lógica conversacional principal
│   │
│   └── RAG/                     # Sistema RAG
│       ├── vector_store.py      # Gestión de ChromaDB
│       ├── embeddings.py        # Procesamiento de documentos
│       ├── retriever.py         # Búsqueda vectorial
│       ├── ingest_documents.py  # Script de ingesta
│       └── knowledge_base/      # Base de conocimiento (4 docs .md)
│           ├── protocolos_emergencias.md
│           ├── sectores_informacion.md
│           ├── contactos_cooperativa.md
│           └── faq_preguntas_frecuentes.md
│
├── ModuloBoletas/               # Módulo adicional (pendiente)
│   └── __init__.py
│
├── Doc/                         # Documentación
│   ├── Documentacion-Emergencia.md  # 929 líneas - Doc técnica completa
│   └── Project.context.md           # Este archivo
│
├── Tests/                       # Tests adicionales organizados
│   ├── test_api.py              # Tests de API REST
│   └── ...                      # Más tests por módulo
│
├── INICIO_RAPIDO.md             # Guía de inicio rápido
├── RESUMEN_EQUIPO.md            # Resumen para el equipo
├── INSTALACION.md               # Instrucciones de instalación
├── DEPENDENCIAS.md              # Explicación de dependencias
└── REPORTE_COBERTURA.md         # Análisis de cobertura de tests (58%)
```

---

## 🔄 Flujo Conversacional del Chatbot

### Estados de Conversación

El chatbot sigue una máquina de estados basada en el diagrama de flujo:

1. **iniciada** → Saludo inicial y explicación
2. **recolectando_datos** → Recopila datos X1-X7 mediante preguntas
3. **calculando_prioridad** → Determina prioridad (baja/media/alta/crítica)
4. **solicitando_contacto** → Pregunta si desea ser contactado
5. **finalizada** → Conversación completa, emergencia creada
6. **cancelada** → Usuario cancela el proceso

### Datos Recolectados (X1-X7)

| Dato | Descripción | Requerido | Uso |
|------|-------------|-----------|-----|
| X1 | Sector | Sí | Identificar ubicación geográfica |
| X2 | Datos del medidor/fuga | Sí | Detalles técnicos del problema |
| X3 | Fecha | Auto | Timestamp del reporte |
| X4 | Nombre usuario | Sí | Identificación del reportante |
| X5 | Fotografía | No | Evidencia visual (opcional) |
| X6 | Dirección | Sí | Ubicación exacta |
| X7 | Teléfono | Sí | Contacto para seguimiento |

### Cálculo de Prioridad

**Crítica**: Corte total de suministro  
**Alta**: Rotura de matriz, cañería rota  
**Media**: Fuga de agua, baja presión  
**Baja**: Agua contaminada, otros problemas

---

## 🗄️ Modelos de Base de Datos

### 1. Emergencia
```python
- id_emergencia: UUID (PK)
- sector: CharField (7 opciones: anibana, el_molino, etc.)
- tipo_emergencia: CharField (7 tipos: rotura_matriz, fuga_agua, etc.)
- descripcion: TextField
- direccion: CharField
- nombre_usuario: CharField
- telefono: CharField (formato +56...)
- fotografia: URLField (opcional)
- nivel_prioridad: CharField (calculado automáticamente)
- fecha_reporte: DateTimeField (auto)
- fecha_actualizacion: DateTimeField (auto)
```

### 2. ChatConversation
```python
- id: BigAutoField (PK)
- session_id: UUIDField (unique)
- estado: CharField (6 estados)
- datos_recolectados: JSONField (almacena X1-X7)
- emergencia: ForeignKey (nullable, se crea al final)
- fecha_inicio/fin: DateTimeField
```

### 3. ChatMessage
```python
- id: BigAutoField (PK)
- conversation: ForeignKey
- rol: CharField ('usuario' o 'asistente')
- contenido: TextField
- timestamp: DateTimeField
```

---

## 🔌 API REST

### Endpoints Principales

**Chat**
- `POST /api/emergencias/chat/init/` - Iniciar nueva conversación
- `POST /api/emergencias/chat/message/` - Enviar mensaje
- `GET /api/emergencias/chat/status/{session_id}/` - Estado de conversación

**Emergencias**
- `GET /api/emergencias/emergencias/` - Listar emergencias
- `GET /api/emergencias/emergencias/{id}/` - Detalle de emergencia
- `GET /api/emergencias/emergencias/?sector=X&prioridad=Y` - Filtrar

**Estadísticas**
- `GET /api/emergencias/stats/` - Estadísticas generales
- `GET /api/emergencias/rag/stats/` - Estado del sistema RAG

### Autenticación
- Ninguna (prototipo)
- Recomendado para producción: JWT o API Key

---

## 🤖 Sistema RAG (Retrieval-Augmented Generation)

### Propósito
Proporcionar al chatbot contexto relevante de la base de conocimiento para generar respuestas más precisas y específicas de la cooperativa.

### Componentes

**1. Vector Store (ChromaDB)**
- Almacena embeddings de documentos
- Búsqueda por similitud semántica
- Colección: `emergencias_knowledge_base`
- Persistencia: carpeta `chroma_db/`

**2. Embeddings**
- Modelo: `paraphrase-multilingual-MiniLM-L12-v2`
- Genera vectores de 384 dimensiones
- Soporte multilingüe (español)

**3. Document Processor**
- Divide documentos en chunks de 1000 caracteres
- Overlap de 200 caracteres
- Soporta: .txt, .md, .pdf, .docx

**4. Retriever**
- Top-k retrieval (k=5)
- Búsqueda con contexto conversacional
- Filtros por categoría

### Base de Conocimiento Actual

4 documentos markdown (127 chunks totales):
1. **protocolos_emergencias.md** - Procedimientos por tipo de emergencia
2. **sectores_informacion.md** - Información de los 7 sectores
3. **contactos_cooperativa.md** - Números y horarios de contacto
4. **faq_preguntas_frecuentes.md** - Preguntas frecuentes

### Flujo RAG

```
Usuario envía mensaje
        ↓
Retriever busca documentos relevantes (top 5)
        ↓
Construye prompt con: mensaje + contexto RAG + historial
        ↓
Gemini genera respuesta contextualizada
        ↓
Respuesta enviada al usuario
```

---

## 🧪 Testing y Calidad

### Cobertura Actual: **58%**

**Desglose por Componente:**
- Models: 90% ✅
- Serializers: 100% ✅
- Admin: 100% ✅
- URLs: 100% ✅
- Views: 58% ⚠️
- Chatbot Service: 43% ⚠️
- Sistema RAG: 32-42% ⚠️

### Tipos de Tests

1. **Tests Unitarios** (`ModuloEmergencia/tests.py`)
   - 25 tests en total
   - TestCase y APITestCase
   - Mocks de Gemini y RAG

2. **Tests de Integración** (pendiente expandir)
   - Flujos completos E2E
   - Integración con Gemini real
   - Ingesta de documentos

3. **Tests de API** (`Tests/test_api.py`)
   - Requests HTTP reales
   - Validación de responses
   - Flujos de usuario

### Herramientas
- Coverage.py 7.10.6
- Django TestCase
- unittest.mock
- pytest-django

---

## ⚙️ Configuración Clave

### Variables de Entorno (.env)

```env
# Django
SECRET_KEY=tu-secret-key
DEBUG=True

# Gemini API (OBLIGATORIO)
GEMINI_API_KEY=AIzaSy...  # Obtener en https://makersuite.google.com/app/apikey

# CORS (Frontend)
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Database (SQLite por defecto)
# DATABASE_URL=postgresql://...  # Opcional para producción
```

### RAG Configuration (settings.py)

```python
RAG_CONFIG = {
    'chunk_size': 1000,
    'chunk_overlap': 200,
    'top_k_results': 5,
    'embedding_model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    'gemini_model': 'gemini-2.5-flash',
}
```

---

## 🚀 Instalación Rápida

```bash
# 1. Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate    # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar .env
copy .env.example .env
# Editar .env y agregar GEMINI_API_KEY

# 4. Migrar base de datos
python manage.py makemigrations
python manage.py migrate

# 5. Ingestar documentos al RAG
python ModuloEmergencia/RAG/ingest_documents.py

# 6. (Opcional) Crear superusuario
python manage.py createsuperuser

# 7. Iniciar servidor
python manage.py runserver
```

---

## 📝 Casos de Uso Principales

### Caso 1: Usuario Reporta Fuga de Agua

```
Usuario: "Hola, tengo una fuga de agua"
Bot: "¡Hola! Entiendo que hay una emergencia con el agua. ¿En qué sector te encuentras?"
Usuario: "Pedro Aguirre Cerda"
Bot: [Almacena sector] "¿Puedes describirme el problema?"
Usuario: "Hay una fuga grande en la calle principal"
Bot: [Extrae info] "¿En qué dirección exactamente?"
Usuario: "Calle Principal 123"
Bot: "¿Cuál es tu nombre?"
Usuario: "Juan Pérez"
Bot: "¿Tienes un teléfono de contacto?"
Usuario: "+56912345678"
Bot: [Calcula prioridad: MEDIA] "Emergencia registrada con prioridad MEDIA. ¿Deseas que te contactemos?"
Usuario: "Sí"
Bot: [Crea emergencia] "Perfecto, te contactaremos pronto al +56912345678"
```

### Caso 2: Usuario Consulta Información

```
Usuario: "¿Cuál es el horario de atención?"
Bot: [Busca en RAG: contactos_cooperativa.md]
    "El horario de atención es de lunes a viernes de 8:00 a 18:00..."
```

---

## 🎯 Roadmap y Mejoras Futuras

### Corto Plazo (Esta semana)
- ✅ Configurar Gemini 2.5 Flash
- ✅ Crear suite de tests básica
- ✅ Generar reporte de cobertura
- 🔄 Aumentar cobertura a 70%
- 🔄 Corregir tests con errores

### Mediano Plazo (Próximas 2 semanas)
- ⬜ Tests de integración E2E completos
- ⬜ Mejorar sistema RAG (cobertura 80%+)
- ⬜ Implementar manejo de archivos (fotos)
- ⬜ Dashboard de administración mejorado
- ⬜ Documentación de API (Swagger/OpenAPI)

### Largo Plazo (Este mes)
- ⬜ Módulo de Boletas (segundo chatbot)
- ⬜ Sistema de notificaciones
- ⬜ Métricas y analytics
- ⬜ Deploy en servidor
- ⬜ CI/CD pipeline

---

## 👥 Equipo

**Backend (2 desarrolladores)**
- Desarrollo de API REST
- Integración con Gemini
- Sistema RAG
- Base de datos
- Testing

**Frontend (2 desarrolladores)**
- Interfaz de chat
- Consumo de API
- UI/UX
- Validaciones cliente

---

## 📚 Recursos y Documentación

### Documentación del Proyecto
- `INICIO_RAPIDO.md` - Guía rápida para empezar
- `INSTALACION.md` - Instrucciones detalladas de setup
- `DEPENDENCIAS.md` - Explicación de requirements.txt
- `Doc/Documentacion-Emergencia.md` - Documentación técnica completa (929 líneas)
- `RESUMEN_EQUIPO.md` - Resumen para el equipo
- `REPORTE_COBERTURA.md` - Análisis de cobertura de tests

### Documentación Externa
- Django: https://docs.djangoproject.com
- DRF: https://www.django-rest-framework.org
- Gemini API: https://ai.google.dev
- LangChain: https://python.langchain.com
- ChromaDB: https://docs.trychroma.com

---

## 🐛 Problemas Conocidos

1. **Tests con errores** (11 tests)
   - Nombres de campos incorrectos en modelos
   - Status codes esperados vs reales
   - Necesitan corrección

2. **Cobertura baja en componentes críticos**
   - Chatbot service: 43%
   - Sistema RAG: 32-42%
   - Ingest documents: 0%

3. **Sin autenticación**
   - Prototipo abierto
   - Implementar JWT para producción

4. **Sin manejo de imágenes**
   - Campo fotografia existe pero no se sube
   - Implementar storage (S3/local)

---

## 🔒 Seguridad

### Consideraciones Actuales (Prototipo)
- ⚠️ Sin autenticación
- ⚠️ DEBUG=True en desarrollo
- ⚠️ SECRET_KEY simple
- ⚠️ CORS abierto a localhost

### Recomendaciones para Producción
- ✅ JWT authentication
- ✅ DEBUG=False
- ✅ SECRET_KEY aleatorio y seguro
- ✅ CORS restringido a dominio específico
- ✅ HTTPS obligatorio
- ✅ Rate limiting
- ✅ Input validation estricta
- ✅ SQL injection protection (Django ORM)
- ✅ XSS protection (Django templates)

---

## 📊 Métricas del Proyecto

**Líneas de Código**
- Python: ~2,500 líneas
- Tests: ~500 líneas
- Documentación: ~2,000 líneas

**Archivos**
- Modelos: 3
- ViewSets: 2
- Serializers: 4
- Services: 1 (534 líneas)
- RAG components: 4
- Tests: 25 unitarios + integración
- Documentos MD: 4 (base conocimiento)

**Dependencias**
- Python packages: 25 directos, ~100 totales
- Tamaño descarga: ~2-3 GB

---

## 🎓 Notas para Desarrolladores

### Agregar Nueva Funcionalidad

1. **Modelo nuevo**: 
   - Crear en `models.py`
   - Ejecutar `makemigrations` y `migrate`
   - Agregar a `admin.py`

2. **Endpoint nuevo**:
   - Serializer en `serializers.py`
   - ViewSet/View en `views.py`
   - URL en `urls.py`
   - Tests en `tests.py`

3. **Documento RAG nuevo**:
   - Crear .md en `RAG/knowledge_base/`
   - Ejecutar `ingest_documents.py`
   - Verificar con `rag/stats/` endpoint

### Debugging

```python
# Logging en chatbot_service.py
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Datos recolectados: {datos}")

# Ver logs en consola
python manage.py runserver --verbosity=2

# Inspeccionar ChromaDB
from ModuloEmergencia.RAG.vector_store import get_vector_store
vs = get_vector_store()
print(vs.get_all_documents())
```

---

**Última actualización**: 5 de Diciembre, 2025  
**Versión**: 1.0.0 (Prototipo)  
**Estado**: Funcional - En desarrollo activo
