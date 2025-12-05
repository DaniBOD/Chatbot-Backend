# 🚀 Guía Rápida de Inicio - Chatbot de Emergencias

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

```bash
python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py
```

Deberías ver:
```
✅ Documentos ingresados exitosamente
📊 Total de documentos en colección: 127
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

---

## 📚 Documentación Completa

Ver: `Backend/Doc/Documentacion-Emergencia.md`

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
