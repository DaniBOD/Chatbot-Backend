# 📦 DEPENDENCIAS DEL PROYECTO

## Resumen de `requirements.txt`

Este archivo contiene **TODAS** las dependencias necesarias para el proyecto. Un simple `pip install -r requirements.txt` instalará todo automáticamente.

---

## 🎯 Paquetes Principales (26 total)

### 1️⃣ **Framework Django** (8 paquetes)
```
asgiref==3.8.1              # Soporte ASGI para Django
Django==5.2.8               # Framework web principal
django-cors-headers==4.6.0  # Manejo de CORS para frontend
djangorestframework==3.16.1 # API REST
python-dotenv==1.0.1        # Variables de entorno (.env)
pytz==2024.2                # Zonas horarias
sqlparse==0.5.3             # Parser SQL
tzdata==2024.2              # Datos de zonas horarias
```

**¿Para qué?** Construir el servidor web, API REST, manejar requests del frontend

---

### 2️⃣ **Inteligencia Artificial / LLM** (4 paquetes)
```
google-generativeai==0.8.3  # ⭐ Gemini API (Google)
langchain==0.3.27           # Framework para LLMs (actualizado)
langchain-google-genai==2.0.10 # Integración LangChain + Gemini (actualizado)
langchain-community==0.3.31 # Integraciones adicionales LangChain (actualizado)
```

**¿Para qué?** Conectar con Gemini, procesar lenguaje natural, extraer datos de conversaciones

---

### 3️⃣ **Sistema RAG (Retrieval-Augmented Generation)** (3 paquetes)
```
chromadb==1.3.5             # ⭐ Base de datos vectorial (precompilada, mejor performance)
sentence-transformers==5.1.2 # ⭐ Crear embeddings multilingües (actualizado)
unstructured==0.18.21       # ⭐ Carga universal de documentos (markdown, PDF, etc.)
```

**¿Para qué?** Buscar información relevante en la base de conocimiento, respuestas contextualizadas

**Mejoras en versiones actualizadas:**
- ChromaDB 1.3.5: Instalación precompilada (sin necesidad de compilar C++), mejor rendimiento
- Sentence Transformers 5.1.2: Soporte mejorado para modelos multilingües
- Unstructured 0.18.21: Simplifica la carga de documentos markdown para RAG

---

### 4️⃣ **Procesamiento de Documentos** (3 paquetes)
```
pypdf==5.1.0                # Leer archivos PDF
python-docx==1.1.2          # Leer archivos Word (.docx)
markdown==3.7               # Procesar archivos Markdown
```

**¿Para qué?** Ingestar documentos de conocimiento al RAG (PDF, DOCX, MD, TXT)

---

### 5️⃣ **Utilidades y Dependencias** (8 paquetes)
```
Pillow==11.0.0              # Procesamiento de imágenes
requests==2.32.3            # HTTP requests
httpx==0.28.1               # HTTP cliente moderno
numpy==2.3.5                # Computación numérica (actualizado)
torch==2.9.1                # PyTorch para transformers (actualizado)
transformers>=4.30.0        # Modelos de Hugging Face
pydantic>=2.0.0             # Validación de datos
typing-extensions>=4.5.0    # Type hints extendidos
```

**¿Para qué?** Soporte para procesamiento de embeddings, validación, HTTP

---

## 🚀 Instalación Única

```bash
pip install -r requirements.txt
```

**Esto instala:**
- ✅ 26 paquetes principales
- ✅ ~100 dependencias adicionales (automáticas)
- ⏱️ Tiempo: 2-5 minutos

---

## 🔍 Paquetes Críticos (Debes entender estos)

| Paquete | Versión | Propósito | Documentación |
|---------|---------|-----------|---------------|
| **Django** | 5.2.8 | Framework web | [docs.djangoproject.com](https://docs.djangoproject.com) |
| **DRF** | 3.16.1 | API REST | [django-rest-framework.org](https://www.django-rest-framework.org) |
| **Gemini** | 0.8.3 | LLM de Google | [ai.google.dev](https://ai.google.dev) |
| **LangChain** | 0.3.27 | Framework LLM | [python.langchain.com](https://python.langchain.com) |
| **ChromaDB** | 1.3.5 | Vector DB | [docs.trychroma.com](https://docs.trychroma.com) |
| **Sentence Transformers** | 5.1.2 | Embeddings | [sbert.net](https://www.sbert.net) |
| **PyTorch** | 2.9.1 | Deep Learning | [pytorch.org](https://pytorch.org) |
| **NumPy** | 2.3.5 | Computación numérica | [numpy.org](https://numpy.org) |

---

## 📊 Distribución de Paquetes

```
Framework Django:        31% (8/26)
IA/LLM:                  15% (4/26)
Sistema RAG:             12% (3/26)
Procesamiento Docs:      12% (3/26)
Utilidades:              31% (8/26)
```

---

## ⚙️ Configuración Especial

### Gemini API Key
```env
GEMINI_API_KEY=tu_api_key
```
👉 Obtener en: https://makersuite.google.com/app/apikey

### ChromaDB
- Carpeta: `chroma_db/`
- Colecciones:
  - `emergencias_knowledge_base` (ModuloEmergencia)
  - `boletas_knowledge_base` (ModuloBoletas)
- Modelo embeddings: `paraphrase-multilingual-MiniLM-L12-v2`
- Versión: 1.3.5 (precompilada, sin necesidad de compilar C++)

---

## 🔄 Actualizar Dependencias

### Ver versiones instaladas
```bash
pip list
```

### Actualizar todo
```bash
pip install -r requirements.txt --upgrade
```

### Actualizar un paquete específico
```bash
pip install google-generativeai --upgrade
```

---

## 🐛 Problemas Comunes

### Error: "Microsoft Visual C++ required"
**Solución:** Instalar [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Error: "error: Microsoft Visual C++ 14.0 is required"
**Solución:** Instalar [Build Tools para Visual Studio](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)

### Error: "Could not find a version that satisfies torch"
**Solución:** Instalar PyTorch primero:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### Error: "pip not found"
**Solución:** Actualizar pip:
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

---

## 📦 Tamaño Aproximado de Descarga

- **requirements.txt:** 26 paquetes principales
- **Dependencias totales:** ~100 paquetes
- **Tamaño de descarga:** ~2-3 GB
- **Espacio en disco:** ~5-7 GB (incluye modelos de ML)

**Nota:** Los modelos de Sentence Transformers (~400 MB) se descargan automáticamente la primera vez que se usan.

---

## ✅ Verificar Instalación

```bash
python -c "import django; print(f'Django: {django.__version__}')"
python -c "import google.generativeai as genai; print('Gemini: OK')"
python -c "import chromadb; print('ChromaDB: OK')"
python -c "import sentence_transformers; print('Transformers: OK')"
python -c "import langchain; print(f'LangChain: {langchain.__version__}')"
```

**Deberías ver:**
```
Django: 5.2.8
Gemini: OK
ChromaDB: OK
Transformers: OK
LangChain: 0.3.27
```

---

## 🎯 Conclusión

El archivo `requirements.txt` está **completo** y contiene todo lo necesario para:
- ✅ Configurar el backend Django
- ✅ Conectar con Gemini API
- ✅ Implementar el sistema RAG
- ✅ Procesar documentos
- ✅ Exponer API REST para frontend

**No necesitas instalar nada manualmente.** Todo está en el archivo.

---

## 📚 Referencias

- **Documentación Módulo Emergencias:** `Doc/Documentacion-Emergencia.md`
- **Documentación Módulo Boletas:** `Doc/Documentacion-Boletas.md`
- **Guía de instalación:** `INSTALACION.md`
- **Resumen para equipo:** `RESUMEN_EQUIPO.md`
- **Inicio rápido:** `INICIO_RAPIDO.md`
