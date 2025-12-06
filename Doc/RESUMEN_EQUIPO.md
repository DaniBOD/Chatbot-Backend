# 📋 Resumen para el Equipo - Chatbot Cooperativa de Agua Potable

## 👥 Equipo del Proyecto
- **2 Frontend**: Interfaz de chat única
- **1 Backend (Emergencias)**: Sistema RAG + Chatbot ✅ COMPLETO
- **1 Backend (Boletas)**: Sistema RAG + Chatbot ✅ COMPLETO

---

## ✅ Estado del Proyecto

### Módulo de Emergencias: **100% COMPLETO**

#### Lo que está implementado:
1. ✅ **Sistema RAG completo** con ChromaDB
2. ✅ **Integración con Google Gemini** (LLM)
3. ✅ **Chatbot conversacional** siguiendo el flujo del diagrama
4. ✅ **Base de datos** con 3 modelos (Emergencia, ChatConversation, ChatMessage)
5. ✅ **API REST completa** con 8+ endpoints
6. ✅ **Base de conocimiento** (protocolos, sectores, contactos, FAQ)
7. ✅ **Admin panel** de Django configurado
8. ✅ **Documentación completa**
9. ✅ **25 tests unitarios** pasando

### Módulo de Boletas: **100% COMPLETO**

#### Lo que está implementado:
1. ✅ **Sistema RAG completo** con ChromaDB (3 documentos, 13 chunks)
2. ✅ **Integración con Google Gemini** (LLM)
3. ✅ **Chatbot conversacional** siguiendo el flujo del diagrama
4. ✅ **Base de datos** con 3 modelos (Boleta, ChatConversation, ChatMessage)
5. ✅ **API REST completa** con 11+ endpoints
6. ✅ **Base de conocimiento** (guía de boletas, tarifas, FAQ)
7. ✅ **Admin panel** de Django configurado
8. ✅ **Documentación completa**
9. ✅ **35 tests unitarios** pasando
10. ✅ **Management command** para ingesta de documentos
11. ✅ **Validación de RUT chileno**
12. ✅ **Consultas comparativas** entre períodos

---

## 🚀 Para Empezar (IMPORTANTE)

### 1. Instalar Dependencias
```bash
cd Backend
pip install -r requirements.txt
```

### 2. Configurar API Key de Gemini
**MUY IMPORTANTE**: Necesitas obtener una API key gratuita de Google Gemini:

1. Ir a: https://makersuite.google.com/app/apikey
2. Crear/copiar tu API key
3. Editar archivo `.env`:
```
GEMINI_API_KEY=tu_api_key_aqui
```

### 3. Crear Base de Datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Ingestar Documentos al RAG

**Módulo Emergencias:**
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

**Módulo Boletas:**
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

### 5. Iniciar Servidor
```bash
python manage.py runserver
```

Servidor: **http://localhost:8000**

---

## 🌐 API Para el Frontend

### Endpoints Principales

#### 1. Iniciar Chat
```http
POST http://localhost:8000/api/emergencias/chat/init/
Content-Type: application/json

{}
```

**Response:**
```json
{
  "session_id": "uuid-aqui",
  "message": "¡Hola! Soy el asistente virtual...",
  "estado": "iniciada"
}
```

#### 2. Enviar Mensaje
```http
POST http://localhost:8000/api/emergencias/chat/message/
Content-Type: application/json

{
  "session_id": "uuid-aqui",
  "message": "Tengo una fuga de agua en El Molino"
}
```

**Response:**
```json
{
  "session_id": "uuid-aqui",
  "message": "Entiendo que tienes una fuga en El Molino. ¿Cuál es tu dirección exacta?",
  "estado": "recolectando_datos",
  "completed": false,
  "datos_recolectados": ["sector", "descripcion"],
  "datos_faltantes": ["nombre_usuario", "telefono", "direccion"]
}
```

#### 3. Verificar Estado
```http
GET http://localhost:8000/api/emergencias/chat/status/{session_id}/
```

---

## 💻 Ejemplo de Integración Frontend (React)

```javascript
// Estado
const [sessionId, setSessionId] = useState(null);
const [messages, setMessages] = useState([]);
const [isCompleted, setIsCompleted] = useState(false);

// 1. Iniciar chat
const initChat = async () => {
  const response = await fetch('http://localhost:8000/api/emergencias/chat/init/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  
  const data = await response.json();
  setSessionId(data.session_id);
  setMessages([{ role: 'bot', content: data.message }]);
};

// 2. Enviar mensaje
const sendMessage = async (userMessage) => {
  // Agregar mensaje del usuario a la UI
  setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
  
  // Enviar al backend
  const response = await fetch('http://localhost:8000/api/emergencias/chat/message/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message: userMessage
    })
  });
  
  const data = await response.json();
  
  // Agregar respuesta del bot
  setMessages(prev => [...prev, { role: 'bot', content: data.message }]);
  
  // Verificar si completó
  if (data.completed) {
    setIsCompleted(true);
  }
};

// 3. Componente de Chat
function ChatInterface() {
  const [input, setInput] = useState('');
  
  useEffect(() => {
    initChat();
  }, []);
  
  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };
  
  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      
      <div className="input-area">
        <input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Escribe tu mensaje..."
          disabled={isCompleted}
        />
        <button onClick={handleSend} disabled={isCompleted}>
          Enviar
        </button>
      </div>
      
      {isCompleted && (
        <button onClick={initChat}>Nueva Conversación</button>
      )}
    </div>
  );
}
```

---

## 🔄 Flujo Completo del Chatbot

1. **Usuario**: "Hola, tengo una fuga de agua"
   - **Bot**: "¿En qué sector vives?"

2. **Usuario**: "En El Molino, calle Principal 123"
   - **Bot**: "¿Cuál es tu nombre?"

3. **Usuario**: "Juan Pérez"
   - **Bot**: "¿Cuál es tu teléfono?"

4. **Usuario**: "912345678"
   - **Bot**: "¿El medidor está corriendo?"

5. **Usuario**: "Sí, muy rápido"
   - **Bot**: "✅ Emergencia registrada. ID: xxx. Prioridad: ALTA. ¿Deseas contactos?"

6. **Usuario**: "Sí"
   - **Bot**: "📞 Contactos: Emergencias +56 9 5403 8948..."

---

## 🎨 Diseño Recomendado para Frontend

### Interfaz Simple de Chat

```
┌─────────────────────────────────────────┐
│  Cooperativa de Agua Potable            │
│  Chatbot de Emergencias                 │
├─────────────────────────────────────────┤
│                                         │
│  🤖 Bot: ¡Hola! Soy el asistente...    │
│                                         │
│           Usuario: Tengo una fuga 👤   │
│                                         │
│  🤖 Bot: ¿En qué sector vives?         │
│                                         │
│           Usuario: El Molino 👤        │
│                                         │
│  🤖 Bot: ¿Cuál es tu dirección?        │
│                                         │
├─────────────────────────────────────────┤
│  [Escribe tu mensaje...]        [Enviar]│
└─────────────────────────────────────────┘
```

### Elementos visuales sugeridos:
- ✅ Burbujas diferenciadas (bot/usuario)
- ✅ Colores: Azul para bot, Gris para usuario
- ✅ Indicador "escribiendo..." mientras espera respuesta
- ✅ Scroll automático a último mensaje
- ✅ Formateo de markdown (negrita, listas, emojis)
- ✅ Botón "Nueva conversación" al finalizar

---

## 📊 Endpoints Adicionales (Opcional)

### Listar Emergencias (para admin)
```http
GET http://localhost:8000/api/emergencias/emergencias/
```

### Estadísticas
```http
GET http://localhost:8000/api/emergencias/emergencias/estadisticas/
```

### Filtrar emergencias
```http
GET http://localhost:8000/api/emergencias/emergencias/?estado=pendiente&sector=el_molino
```

---

## 🛠️ Para tu Compañero (Módulo Boletas)

El proyecto ya tiene la estructura para el módulo de boletas:
- `Backend/ModuloBoletas/` (estructura básica creada)
- Puede seguir el mismo patrón que ModuloEmergencia
- URLs ya configuradas: `/api/boletas/`

---

## ⚙️ Configuración (Solo para prototipo)

### SQLite (Ya configurado)
- Base de datos: `db.sqlite3`
- No requiere instalación adicional
- Perfecta para prototipo/demo

### CORS (Ya configurado)
- Frontend en: `http://localhost:5173` (Vite)
- Frontend en: `http://localhost:3000` (Create React App)

---

## 🧪 Probar el Sistema

### Opción 1: cURL
```bash
# Iniciar
curl -X POST http://localhost:8000/api/emergencias/chat/init/ -H "Content-Type: application/json" -d '{}'

# Enviar mensaje
curl -X POST http://localhost:8000/api/emergencias/chat/message/ \
  -H "Content-Type: application/json" \
  -d '{"session_id":"TU_SESSION_ID","message":"Tengo una fuga"}'
```

### Opción 2: Postman
Importar colección con los endpoints arriba

### Opción 3: Admin Panel
- URL: http://localhost:8000/admin/
- Crear superusuario: `python manage.py createsuperuser`
- Ver emergencias, conversaciones, mensajes

---

## 📁 Estructura del Proyecto

```
Backend/
├── chatbot_backend/          # Configuración Django
├── ModuloEmergencia/         # 🔥 Módulo Emergencias (completo)
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── admin.py
│   ├── services/
│   │   └── chatbot_service.py
│   └── RAG/
│       ├── vector_store.py
│       ├── embeddings.py
│       ├── retriever.py
│       ├── ingest_documents.py
│       └── knowledge_base/
│           ├── protocolos_emergencias.md
│           ├── sectores_informacion.md
│           ├── contactos_cooperativa.md
│           └── faq_preguntas_frecuentes.md
├── ModuloBoletas/            # 💳 Módulo Boletas (completo)
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   ├── services/
│   │   └── chatbot_service.py
│   ├── RAG/
│   │   ├── vector_store.py
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   ├── ingest_documents.py
│   │   └── knowledge_base/
│   │       ├── guia_boletas.md
│   │       ├── tarifas.md
│   │       └── preguntas_frecuentes.md
│   └── management/
│       └── commands/
│           └── ingest_knowledge_base.py
├── manage.py
├── requirements.txt
├── .env
└── Doc/
    ├── Documentacion-Emergencia.md
    └── Documentacion-Boletas.md
```

---

## 🐛 Solución de Problemas Comunes

### Error: "GEMINI_API_KEY not configured"
**Solución**: Configurar en `.env`

### Error: "No module named 'chromadb'"
**Solución**: `pip install -r requirements.txt`

### RAG vacío (0 documentos)
**Solución**: Ejecutar ingesta:
```bash
python manage.py shell < ModuloEmergencia/RAG/ingest_documents.py
```

### CORS error en frontend
**Solución**: Verificar que el frontend esté en:
- `http://localhost:5173` o
- `http://localhost:3000`

### Error 404 en API
**Solución**: Asegurarse de incluir `/api/emergencias/` en la URL

---

## 📞 Contactos del Proyecto

### Datos de la Cooperativa (en el chatbot)
- Emergencias 24/7: **+56 9 5403 8948**
- Recaudación: **+56 9 8149 4350**
- Gerencia: **+56 9 7846 7011**
- Email: laciacoop@gmail.com

### Sectores Disponibles
1. Anibana
2. El Molino
3. La Compañía
4. El Maitén 1
5. La Morera
6. El Maitén 2
7. Santa Margarita

---

## 🎯 Prioridades de Emergencias

El chatbot calcula automáticamente:
- 🔴 **CRÍTICA**: Rotura matriz, sin agua → Atención inmediata
- 🟠 **ALTA**: Agua contaminada, cañería rota → Mismo día
- 🟡 **MEDIA**: Fugas moderadas → 1-3 días
- 🟢 **BAJA**: Consultas generales → 3-5 días

---

## 📝 Checklist Pre-Demo

- [ ] `pip install -r requirements.txt`
- [ ] Configurar GEMINI_API_KEY en `.env`
- [ ] `python manage.py migrate`
- [ ] Ejecutar script de ingesta RAG
- [ ] `python manage.py runserver`
- [ ] Probar endpoint `/api/emergencias/chat/init/`
- [ ] Crear superusuario (opcional)
- [ ] Probar conversación completa
- [ ] Verificar que se crea la emergencia en admin

---

## 🚀 Para la Demo/Presentación

1. **Mostrar el flujo completo**:
   - Iniciar chat
   - Reportar emergencia
   - Mostrar cálculo de prioridad
   - Obtener contactos

2. **Mostrar el admin**:
   - Emergencias registradas
   - Conversaciones
   - Historial de mensajes

3. **Explicar la tecnología**:
   - RAG: Base de conocimiento inteligente
   - Gemini: Procesamiento de lenguaje natural
   - Django REST: API robusta

---

## 📚 Documentación Completa

- **Inicio Rápido**: `INICIO_RAPIDO.md`
- **Documentación Técnica**: `Doc/Documentacion-Emergencia.md`
- **README**: `README`

---

**¡Éxito con el proyecto! 🎉**

El módulo de emergencias está 100% funcional y listo para integrar con el frontend.
