# 🚀 GUÍA DE INSTALACIÓN COMPLETA

## ✅ Pre-requisitos

- Python 3.10 o superior
- pip (instalador de paquetes de Python)
- Git

---

## 📋 PASOS DE INSTALACIÓN

### 1️⃣ Clonar el Repositorio (si aún no lo has hecho)

```bash
git clone https://github.com/DaniBOD/Chatbot-Backend.git
cd Chatbot-Backend/Backend
```

---

### 2️⃣ Crear Entorno Virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Verificar que el entorno esté activo:**
- Deberías ver `(venv)` al inicio de tu terminal

---

### 3️⃣ Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Esto instalará:**
- Django 5.2.8 (Framework web)
- Django REST Framework (API REST)
- Google Generative AI (Gemini)
- LangChain (Framework para LLMs)
- ChromaDB (Base de datos vectorial)
- Sentence Transformers (Embeddings)
- Y más dependencias necesarias...

**⏱️ Tiempo estimado:** 2-5 minutos dependiendo de tu conexión

---

### 4️⃣ Configurar Variables de Entorno

#### A. Crear archivo .env
```bash
copy .env.example .env
```

#### B. Obtener API Key de Gemini (OBLIGATORIO)

1. **Ir a:** https://makersuite.google.com/app/apikey
2. **Iniciar sesión** con tu cuenta de Google
3. **Hacer clic** en "Create API Key"
4. **Copiar** la API key generada

#### C. Editar archivo .env

Abrir el archivo `.env` y reemplazar:
```env
GEMINI_API_KEY=tu_api_key_aqui
```

Por:
```env
GEMINI_API_KEY=TU_KEY_REAL_AQUI
```

**Ejemplo:**
```env
GEMINI_API_KEY=AIzaSyBX1234567890abcdefghijklmnopqrst
```

---

### 5️⃣ Crear Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

**Esto creará:**
- Archivo `db.sqlite3` (base de datos SQLite)
- Tablas para: Emergencias, Conversaciones, Mensajes

---

### 6️⃣ Ingestar Documentos al Sistema RAG

Cada módulo requiere su propio comando de ingesta:

#### A. Ingestar Módulo Emergencias
```bash
python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py
```

**Deberías ver:**
```
=== Iniciando ingesta de documentos ===
Procesando documentos...
✅ Documentos ingresados exitosamente
📊 Total de documentos en colección: ~127
```

#### B. Ingestar Módulo Boletas
```bash
python manage.py ingest_knowledge_base
```

**Deberías ver:**
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

**Si ambas ingestas fueron exitosas, ¡perfecto! El RAG está listo para ambos módulos.**

---

### 7️⃣ Crear Superusuario (Opcional)

Para acceder al panel de administración:

```bash
python manage.py createsuperuser
```

Te pedirá:
- Username
- Email (opcional, puedes dejarlo en blanco)
- Password (mínimo 8 caracteres)

---

### 8️⃣ Iniciar el Servidor

```bash
python manage.py runserver
```

**Deberías ver:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## ✅ VERIFICAR INSTALACIÓN

### Opción 1: Navegador

Abrir en tu navegador:
- **API Root:** http://localhost:8000/api/emergencias/
- **Admin Panel:** http://localhost:8000/admin/ (usar credenciales del superusuario)

### Opción 2: Script de Verificación

En otra terminal (con el servidor corriendo):
```bash
python test_system.py
```

Deberías ver:
```
✅ Configuración
✅ Base de Datos
✅ Sistema RAG
✅ Chatbot Service
✅ Prueba de Integración

🎉 ¡Todos los checks pasaron! El sistema está listo.
```

### Opción 3: Probar API con cURL

```bash
curl -X POST http://localhost:8000/api/emergencias/chat/init/ -H "Content-Type: application/json" -d "{}"
```

Deberías recibir:
```json
{
  "session_id": "uuid-aqui",
  "message": "¡Hola! Soy el asistente virtual...",
  "estado": "iniciada"
}
```

---

## 🎉 ¡INSTALACIÓN COMPLETA!

Tu backend está listo para:
- ✅ Recibir requests del frontend
- ✅ Procesar conversaciones con el chatbot
- ✅ Usar RAG para respuestas inteligentes
- ✅ Registrar emergencias en la base de datos

---

## 🔧 Comandos Útiles

### Reiniciar base de datos
```bash
python manage.py flush
python manage.py migrate
```

### Reiniciar ChromaDB
```bash
rm -rf chroma_db
python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py
```

### Ver migraciones
```bash
python manage.py showmigrations
```

### Crear nueva migración
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🐛 Solución de Problemas

### Error: "No module named 'xxx'"
**Solución:**
```bash
pip install -r requirements.txt
```

### Error: "GEMINI_API_KEY not configured"
**Solución:**
1. Verificar que `.env` existe
2. Verificar que `GEMINI_API_KEY` tiene un valor
3. Reiniciar el servidor

### Error: "No such table: ModuloEmergencia_emergencia"
**Solución:**
```bash
python manage.py makemigrations
python manage.py migrate
```

### Error: ChromaDB vacío (0 documentos)
**Solución:**
```bash
python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py
```

### Error: CORS en el frontend
**Solución:** Verificar que en `.env` esté la URL de tu frontend:
```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Error: Puerto 8000 en uso
**Solución:** Usar otro puerto:
```bash
python manage.py runserver 8001
```

---

## 📞 Soporte

Si tienes problemas:
1. Leer `RESUMEN_EQUIPO.md`
2. Revisar `Doc/Documentacion-Emergencia.md`
3. Verificar que seguiste todos los pasos

---

## 🎯 Próximos Pasos

1. ✅ Backend instalado
2. 🔜 Integrar con Frontend
3. 🔜 Probar flujo completo
4. 🔜 Preparar demo

**¡Éxito con el proyecto! 🚀**
