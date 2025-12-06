# 🚀 Guía Rápida de Inicio - Chatbot Cooperativa de Agua Potable

## 📦 Módulos Disponibles

- **ModuloEmergencia**: Reportar emergencias de servicio de agua
- **ModuloBoletas**: Consultar información de boletas de consumo

---

## ✅ Pasos para Iniciar el Proyecto

### 1. Instalar Dependencias

```bash
cd Backend
pip install -r requirements.txt
```

### 2. Configurar API Key de Gemini

1. Obtener API key en: https://makersuite.google.com/app/apikey
2. Editar archivo `.env`:
```env
GEMINI_API_KEY=tu_api_key_aqui
```

### 3. Crear Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Ingestar Documentos al RAG

Cada módulo tiene su propio proceso de ingesta:

#### Módulo Emergencias
```bash
python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py
```

Deberías ver:
```
=== Iniciando ingesta de documentos ===
Procesando documentos...
✅ Documentos ingresados exitosamente
📊 Total de documentos en colección: ~127
```

#### Módulo Boletas
```bash
python manage.py ingest_knowledge_base
```

Deberías ver:
```
🚀 Iniciando ingesta de documentos...

✅ Ingesta completada exitosamente!
  📁 Archivos procesados: 3
  📄 Chunks generados: 13
  💾 Documentos agregados: 13
```

**Opciones adicionales (solo Boletas):**
```bash
python manage.py ingest_knowledge_base --reset     # Resetear y reingestar
python manage.py ingest_knowledge_base --stats     # Ver estadísticas
python manage.py ingest_knowledge_base --verbose   # Output detallado
```

### 5. Crear Superusuario (Opcional)

```bash
python manage.py createsuperuser
```

### 6. Iniciar Servidor

```bash
python manage.py runserver
```

Servidor disponible en: http://localhost:8000

---

## 🧪 Probar el Chatbot

### Opción 1: Admin Panel

1. Ir a: http://localhost:8000/admin/
2. Login con superusuario
3. Explorar modelos: Emergencias, Conversaciones, Mensajes

### Opción 2: API REST (Postman/cURL)

**Iniciar conversación:**
```bash
curl -X POST http://localhost:8000/api/emergencias/chat/init/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Enviar mensaje:**
```bash
curl -X POST http://localhost:8000/api/emergencias/chat/message/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "tu-session-id",
    "message": "Tengo una fuga de agua en El Molino"
  }'
```

### Opción 3: Python Script

```python
import requests

# Iniciar chat
response = requests.post('http://localhost:8000/api/emergencias/chat/init/')
data = response.json()
session_id = data['session_id']
print("Bot:", data['message'])

# Enviar mensaje
response = requests.post('http://localhost:8000/api/emergencias/chat/message/', json={
    'session_id': session_id,
    'message': 'Hola, tengo una fuga de agua muy grande'
})
print("Bot:", response.json()['message'])
```

---

## 📍 Endpoints Principales

### Módulo de Emergencias
- **Chat:**
  - `POST /api/emergencias/chat/init/` - Iniciar conversación
  - `POST /api/emergencias/chat/message/` - Enviar mensaje
  - `GET /api/emergencias/chat/status/{session_id}/` - Ver estado

- **Emergencias:**
  - `GET /api/emergencias/emergencias/` - Listar emergencias
  - `GET /api/emergencias/emergencias/{id}/` - Ver detalle
  - `GET /api/emergencias/emergencias/estadisticas/` - Estadísticas

- **RAG:**
  - `GET /api/emergencias/rag/stats/` - Estadísticas del sistema RAG

### Módulo de Boletas
- **Chat:**
  - `POST /api/boletas/chat/init/` - Iniciar conversación
  - `POST /api/boletas/chat/message/` - Enviar mensaje
  - `GET /api/boletas/chat/status/{session_id}/` - Ver estado

- **Boletas:**
  - `GET /api/boletas/boletas/` - Listar boletas (con filtros)
  - `GET /api/boletas/boletas/{id}/` - Ver detalle
  - `POST /api/boletas/boletas/consultar/` - Consultar con múltiples criterios

- **RAG:**
  - `GET /api/boletas/rag/stats/` - Estadísticas del sistema RAG

---

## 📚 Documentación Completa

- **Módulo Emergencias**: `Doc/Documentacion-Emergencia.md`
- **Módulo Boletas**: `Doc/Documentacion-Boletas.md`

---

## ⚠️ Solución de Problemas

### Error: "GEMINI_API_KEY not configured"
- Asegúrate de tener el archivo `.env` con tu API key

### Error: "No module named 'chromadb'"
- Ejecuta: `pip install -r requirements.txt`

### Base de datos vacía
- Ejecuta migraciones: `python manage.py migrate`

### RAG sin documentos
- Ejecuta ingesta: `python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py`
- Ejecuta ingesta: `python manage.py ingest_knowledge_base`

---

## 🎯 Próximos Pasos

1. ✅ Obtener API key de Gemini
2. ✅ Configurar `.env`
3. ✅ Ejecutar migraciones
4. ✅ Ingestar documentos
5. ✅ Probar chatbot
6. 🔜 Conectar con Frontend
7. 🔜 Desplegar en producción

---

## 📞 Contacto

- **Repositorio:** https://github.com/DaniBOD/Chatbot-Backend
- **Documentación:** `Doc/Documentacion-Emergencia.md`
