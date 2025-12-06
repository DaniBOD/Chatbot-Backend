# 📊 Reporte de Cobertura de Tests - Módulo Emergencias

**Fecha**: 5 de Diciembre, 2025  
**Proyecto**: Chatbot Backend - Módulo de Emergencias  
**Framework**: Django 5.2.8 + DRF 3.16.1  

---

## 🎯 Resumen Ejecutivo

### Cobertura Global del Módulo
- **Cobertura Total**: **58%** (925 líneas, 392 sin cubrir)
- **Tests Ejecutados**: 25 tests
- **Tests Exitosos**: 7 ✅
- **Tests con Errores**: 11 ⚠️
- **Tests Fallidos**: 7 ❌

---

## 📈 Cobertura por Componente

### ✅ Componentes con Alta Cobertura (≥80%)

| Componente | Cobertura | Líneas | Faltantes | Estado |
|------------|-----------|--------|-----------|---------|
| `admin.py` | **100%** | 20 | 0 | ✅ Excelente |
| `apps.py` | **100%** | 5 | 0 | ✅ Excelente |
| `serializers.py` | **100%** | 47 | 0 | ✅ Excelente |
| `urls.py` | **100%** | 7 | 0 | ✅ Excelente |
| `models.py` | **90%** | 69 | 7 | ✅ Muy Bueno |
| `tests.py` | **80%** | 201 | 40 | ✅ Bueno |

**Análisis**: Los componentes básicos de Django (admin, serializers, URLs, models) tienen excelente cobertura. Esto indica que la arquitectura base está bien testeada.

---

### ⚠️ Componentes con Cobertura Media (40-60%)

| Componente | Cobertura | Líneas | Faltantes | Estado |
|------------|-----------|--------|-----------|---------|
| `views.py` | **58%** | 127 | 53 | ⚠️ Mejorable |
| `chatbot_service.py` | **43%** | 145 | 83 | ⚠️ Mejorable |
| `embeddings.py` | **42%** | 97 | 56 | ⚠️ Mejorable |
| `vector_store.py` | **41%** | 70 | 41 | ⚠️ Mejorable |

**Análisis**: Los servicios principales tienen cobertura insuficiente, especialmente la lógica del chatbot y el sistema RAG.

---

### ❌ Componentes con Baja Cobertura (<40%)

| Componente | Cobertura | Líneas | Faltantes | Estado |
|------------|-----------|--------|-----------|---------|
| `retriever.py` | **32%** | 75 | 51 | ❌ Crítico |
| `ingest_documents.py` | **0%** | 61 | 61 | ❌ Sin tests |

**Análisis Crítico**: El sistema RAG tiene cobertura muy baja. El script de ingesta no tiene tests.

---

## 🔍 Análisis Detallado por Módulo

### 1. **Models (90% - ✅ Muy Bueno)**

**Líneas sin cubrir**: 168, 189-192, 261, 311

**Áreas no testeadas**:
- Método `calcular_prioridad()` en Emergencia
- Validaciones personalizadas
- Métodos `__str__()` en algunos modelos

**Recomendación**: Agregar tests para:
```python
def test_calcular_prioridad_critica(self):
    """Test: Emergencias críticas como corte total"""
    
def test_validacion_telefono_invalido(self):
    """Test: Rechazar teléfonos con formato inválido"""
```

---

### 2. **Views (58% - ⚠️ Mejorable)**

**Líneas sin cubrir**: 64, 68, 79-84, 97-118, 127-140, 163-165, 174-178, 210, 228-230, 299-307, 327-344

**Áreas no testeadas**:
- Manejo de errores en endpoints de chat
- Validaciones de datos en requests
- Filtros avanzados en viewsets
- Acciones personalizadas (custom actions)
- Paginación

**Código crítico sin tests** (líneas 97-118):
```python
def chat_message(request):
    # Lógica de procesamiento de mensajes
    # SIN COBERTURA COMPLETA
```

**Recomendación**: Tests de integración para:
- Manejo de errores 404/500
- Validación de JSON malformado
- Rate limiting (si aplicable)
- Filtros combinados

---

### 3. **Chatbot Service (43% - ⚠️ Mejorable)**

**Líneas sin cubrir**: 48, 122, 125, 150-152, 174-203, 223-254, 266-314, 320-329, 340-361, 367-399, 416-436, 457-466, 479-485, 491, 509-518

**Áreas no testeadas** (CRÍTICO):
- `_extract_data_with_llm()` - Extracción de datos con Gemini
- `_create_emergency_and_ask_contact()` - Creación de emergencia
- `_handle_contact_request()` - Manejo de solicitud de contacto
- `_build_extraction_prompt()` - Construcción de prompts
- `_get_conversation_history()` - Obtención de historial
- Manejo de errores de API de Gemini
- Timeouts y retry logic

**Impacto**: Este es el componente MÁS CRÍTICO del sistema y tiene solo 43% de cobertura.

**Recomendación URGENTE**: Crear suite completa de tests:
```python
def test_extract_data_with_llm_success(self):
def test_extract_data_with_llm_api_error(self):
def test_create_emergency_with_complete_data(self):
def test_handle_contact_request_positive(self):
def test_handle_contact_request_negative(self):
def test_conversation_flow_complete(self):
```

---

### 4. **Sistema RAG (32-42% - ❌ Crítico)**

#### Vector Store (41%)
**Líneas sin cubrir**: 47-52, 73-83, 102-112, 121-131, 140-147, 156-165

**Áreas no testeadas**:
- `add_documents()` - Añadir documentos
- `query()` - Búsqueda vectorial
- `get_all_documents()` - Obtener documentos
- `delete_collection()` - Eliminar colección
- Manejo de errores de ChromaDB

#### Retriever (32%)
**Líneas sin cubrir**: 47-65, 85-94, 106-126, 146-164, 187-206, 219-231, 240

**Áreas no testeadas**:
- `retrieve()` - Recuperación básica
- `retrieve_with_context()` - Recuperación con contexto
- `_build_context()` - Construcción de contexto
- `get_relevant_context_text()` - Texto relevante
- `search_by_category()` - Búsqueda por categoría

#### Embeddings (42%)
**Líneas sin cubrir**: 54-82, 94-116, 152-154, 171-196, 224-228, 237, 270-272

**Áreas no testeadas**:
- `load_document()` - Carga de documentos
- `split_documents()` - División en chunks
- `process_text()` - Procesamiento de texto
- `process_directory()` - Procesamiento de carpetas
- Manejo de diferentes formatos (PDF, DOCX, MD)

#### Ingest Documents (0% - ❌ SIN TESTS)
**Estado**: Archivo completo sin cobertura (61 líneas)

**Impacto**: Script crítico para inicializar el sistema RAG no tiene tests.

**Recomendación CRÍTICA**: Crear tests inmediatamente:
```python
def test_ingest_documents_success(self):
def test_ingest_documents_empty_directory(self):
def test_ingest_documents_invalid_format(self):
def test_ingest_documents_duplicate_handling(self):
```

---

## 🚨 Problemas Identificados en Tests Existentes

### Errores de Modelo (11 errores)

**Problema**: Tests usan campos que no existen en los modelos
```python
# ERROR: ChatMessage no tiene campo 'conversacion', tiene 'conversation'
mensaje = ChatMessage.objects.create(
    conversacion=self.conversation,  # ❌ INCORRECTO
    rol='usuario',
    contenido='Hola'
)

# CORRECTO:
mensaje = ChatMessage.objects.create(
    conversation=self.conversation,  # ✅ CORRECTO
    rol='usuario',
    contenido='Hola'
)
```

**Afectados**: 11 tests de modelos

---

### Errores de API (7 fallos)

**Problema 1**: Status codes incorrectos
```python
# Test espera 200, pero API retorna 201 (Created)
self.assertEqual(response.status_code, 200)  # ❌ FALLA
# Debería ser:
self.assertEqual(response.status_code, 201)  # ✅ CORRECTO
```

**Problema 2**: Mock incompleto del chatbot service
```python
# process_message retorna 3 valores, no 2
response, estado = service.process_message(...)  # ❌ ERROR
# Debería ser:
response, estado, datos = service.process_message(...)  # ✅ CORRECTO
```

**Afectados**: 7 tests de API

---

## 📋 Plan de Acción Recomendado

### Prioridad CRÍTICA (Hacer esta semana)

1. **Corregir tests existentes** (2-3 horas)
   - Arreglar nombres de campos en modelos
   - Ajustar status codes esperados
   - Completar mocks del chatbot service

2. **Crear tests para chatbot_service.py** (4-6 horas)
   - Suite completa de tests unitarios
   - Tests de integración con Gemini
   - Manejo de errores

3. **Tests para ingest_documents.py** (2 horas)
   - Test de ingesta exitosa
   - Test de manejo de errores
   - Test de formatos inválidos

---

### Prioridad ALTA (Hacer próxima semana)

4. **Tests para sistema RAG** (6-8 horas)
   - `vector_store.py`: CRUD de documentos
   - `retriever.py`: Búsquedas vectoriales
   - `embeddings.py`: Procesamiento de documentos

5. **Tests de integración E2E** (4 horas)
   - Flujo completo de conversación
   - Creación de emergencia real
   - Integración con RAG

---

### Prioridad MEDIA (Hacer cuando sea posible)

6. **Aumentar cobertura de views.py** (3-4 horas)
   - Tests de manejo de errores
   - Tests de filtros y paginación
   - Tests de validaciones

7. **Tests de performance** (2-3 horas)
   - Tiempo de respuesta de RAG
   - Carga de múltiples conversaciones
   - Memory leaks

---

## 🎯 Objetivos de Cobertura

### Corto Plazo (Esta semana)
- **Target**: 70% de cobertura
- **Focus**: Chatbot service + ingest_documents

### Mediano Plazo (Próximas 2 semanas)
- **Target**: 80% de cobertura
- **Focus**: Sistema RAG completo

### Largo Plazo (Este mes)
- **Target**: 90% de cobertura
- **Focus**: Tests E2E y edge cases

---

## 📊 Métricas Actuales vs Objetivos

| Métrica | Actual | Objetivo Corto | Objetivo Largo |
|---------|--------|----------------|----------------|
| **Cobertura Total** | 58% | 70% | 90% |
| **Chatbot Service** | 43% | 80% | 95% |
| **Sistema RAG** | 32-42% | 70% | 85% |
| **Views** | 58% | 75% | 90% |
| **Models** | 90% | 95% | 98% |

---

## 🛠️ Herramientas Utilizadas

- **Coverage.py 7.10.6**: Análisis de cobertura
- **Django TestCase**: Tests unitarios
- **DRF APITestCase**: Tests de API REST
- **unittest.mock**: Mocking de Gemini y RAG
- **pytest-django 4.11.1**: Framework de tests
- **pytest-cov 5.0.0**: Plugin de cobertura para pytest

---

## 📁 Archivos Generados

- **Reporte HTML**: `htmlcov/index.html` (abrir en navegador)
- **Datos coverage**: `.coverage` (archivo binario)
- **Este reporte**: `REPORTE_COBERTURA.md`

---

## 🔗 Comandos Útiles

```bash
# Ejecutar todos los tests
python manage.py test ModuloEmergencia

# Ejecutar con cobertura
python -m coverage run --source=ModuloEmergencia manage.py test ModuloEmergencia

# Ver reporte en terminal
python -m coverage report -m

# Generar reporte HTML
python -m coverage html

# Ejecutar test específico
python manage.py test ModuloEmergencia.tests.ChatbotServiceTests.test_start_conversation

# Ver tests con más detalle
python manage.py test ModuloEmergencia --verbosity=2
```

---

## 🎓 Conclusiones

### Fortalezas ✅
1. Arquitectura base bien testeada (admin, serializers, models)
2. Tests estructurados con buena organización
3. Uso de mocks para dependencias externas
4. Cobertura del 90% en models

### Debilidades ⚠️
1. **Chatbot service con solo 43% de cobertura** (componente crítico)
2. **Sistema RAG pobremente testeado** (32-42%)
3. **Script de ingesta sin tests** (0%)
4. 11 tests con errores de implementación
5. Falta de tests de integración E2E

### Recomendación Final 🎯

**Priorizar el testing del chatbot service y sistema RAG antes de desplegar a producción.** Estos componentes son el corazón del sistema y actualmente tienen cobertura insuficiente, lo que representa un riesgo alto de bugs en producción.

La cobertura actual del 58% es **aceptable para un prototipo**, pero **insuficiente para producción**. Se recomienda alcanzar al menos 80% antes de lanzamiento.

---

**Generado automáticamente por Coverage.py**  
**Fecha**: 5 de Diciembre, 2025
