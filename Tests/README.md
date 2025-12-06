# Tests - Suite Completa de Pruebas

## 📋 Descripción

Este directorio contiene una suite completa de tests organizados para el sistema de Chatbot de Emergencias. Los tests están diseñados para mejorar la cobertura del código desde el baseline de 58% hasta 75%+ con enfoque en calidad de prototipo.

---

## 📁 Estructura de Tests

```
Tests/
├── test_chatbot_service.py      # 30+ tests - Servicio principal (ChatbotService)
├── test_rag_system.py            # 35+ tests - Sistema RAG completo
├── test_api_integration.py       # 40+ tests - Integración E2E de APIs
├── test_error_handling.py        # 50+ tests - Manejo de errores y edge cases
├── test_models_extended.py       # 45+ tests - Modelos extendidos
└── README.md                     # Este archivo
```

**Total: ~200 tests adicionales**

---

## 🎯 Objetivos de Cobertura

| Componente | Cobertura Inicial | Meta | Tests Enfocados |
|------------|-------------------|------|-----------------|
| **chatbot_service.py** | 43% | 75%+ | test_chatbot_service.py |
| **Sistema RAG** | 32-42% | 70%+ | test_rag_system.py |
| **Views/API** | 58% | 75%+ | test_api_integration.py |
| **Models** | 90% | 95%+ | test_models_extended.py |
| **Error Handling** | N/A | 80%+ | test_error_handling.py |

---

## 🧪 Descripción de Archivos

### 1. test_chatbot_service.py
**Objetivo**: Cobertura del servicio principal de chatbot (43% → 75%+)

**Incluye:**
- ✅ Tests de inicialización del servicio
- ✅ Tests de `start_conversation()`
- ✅ Tests de `process_message()`
- ✅ Tests de `_extract_data_with_llm()`
- ✅ Tests de transiciones de estado
- ✅ Tests de cálculo de prioridad
- ✅ Tests de creación de emergencias
- ✅ Tests de historial de conversación
- ✅ Tests de manejo de errores
- ✅ Tests de integración con RAG

**Tests totales: ~30**

**Ejemplo de test:**
```python
@patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
def test_start_conversation_creates_new_session(self, mock_llm):
    mock_llm.return_value = "¡Hola! ¿En qué puedo ayudarte?"
    
    service = ChatbotService()
    session_id, estado, respuesta = service.start_conversation()
    
    self.assertIsNotNone(session_id)
    self.assertEqual(estado, 'iniciada')
    self.assertIn("Hola", respuesta)
```

---

### 2. test_rag_system.py
**Objetivo**: Cobertura del sistema RAG (32-42% → 70%+)

**Incluye:**
- ✅ Tests de `vector_store.py` (VectorStore, ChromaDB)
- ✅ Tests de `embeddings.py` (DocumentProcessor)
- ✅ Tests de `retriever.py` (RAGRetriever)
- ✅ Tests de `ingest_documents.py` (ingesta de documentos)
- ✅ Tests de calidad de embeddings
- ✅ Tests de búsqueda semántica
- ✅ Tests de filtros por categoría
- ✅ Tests de manejo de resultados vacíos
- ✅ Tests de división de documentos (chunking)

**Tests totales: ~35**

**Ejemplo de test:**
```python
def test_similar_texts_have_similar_embeddings(self):
    processor = DocumentProcessor()
    
    text1 = "Tengo una fuga de agua en mi casa"
    text2 = "Hay una fuga de agua en mi domicilio"
    text3 = "El clima está soleado hoy"
    
    embeddings = processor.generate_embeddings([text1, text2, text3])
    
    # Textos similares deben tener mayor similitud
    similarity_12 = cosine_similarity(embeddings[0], embeddings[1])
    similarity_13 = cosine_similarity(embeddings[0], embeddings[2])
    
    self.assertGreater(similarity_12, similarity_13)
```

---

### 3. test_api_integration.py
**Objetivo**: Tests de integración end-to-end (E2E)

**Incluye:**
- ✅ Tests de flujo completo de chat
- ✅ Tests de endpoints de emergencias
- ✅ Tests de estadísticas
- ✅ Tests de filtros y búsquedas
- ✅ Tests de historial de conversación
- ✅ Tests de manejo de errores en API
- ✅ Tests de validación de datos
- ✅ Tests de concurrencia
- ✅ Tests de múltiples sesiones

**Tests totales: ~40**

**Ejemplo de test:**
```python
@patch('ModuloEmergencia.services.chatbot_service.ChatbotService._generate_llm_response')
def test_complete_emergency_report_flow(self, mock_llm):
    mock_llm.return_value = "Entendido"
    
    # 1. Iniciar conversación
    response = self.client.post('/api/emergencias/chat/init/')
    session_id = response.data['session_id']
    
    # 2. Recolectar datos
    conversation_steps = [
        "Estoy en Anibana",
        "Hay una fuga de agua",
        "Calle Principal 123",
        "Juan Pérez",
        "+56912345678"
    ]
    
    for mensaje in conversation_steps:
        response = self.client.post('/api/emergencias/chat/message/', {
            'session_id': session_id,
            'mensaje': mensaje
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # 3. Verificar que los datos se acumularon
    conversation = ChatConversation.objects.get(session_id=session_id)
    self.assertIn('sector', conversation.datos_recolectados)
```

---

### 4. test_error_handling.py
**Objetivo**: Robustez y manejo de casos edge

**Incluye:**
- ✅ Tests de validación de inputs (vacíos, muy largos, caracteres especiales)
- ✅ Tests de protección contra SQL injection
- ✅ Tests de protección contra XSS
- ✅ Tests de errores de la API de Gemini (timeout, rate limit, API key inválida)
- ✅ Tests de errores de JSON inválido
- ✅ Tests de errores de estado de conversación
- ✅ Tests de datos incompletos o inválidos
- ✅ Tests de errores del sistema RAG
- ✅ Tests de casos edge (prioridades mixtas, formatos de teléfono)
- ✅ Tests de límites de recursos

**Tests totales: ~50**

**Ejemplo de test:**
```python
@patch('google.generativeai.GenerativeModel.generate_content')
def test_invalid_json_from_llm(self, mock_gemini):
    mock_response = Mock()
    mock_response.text = "Este no es JSON válido {{{["
    mock_gemini.return_value = mock_response
    
    result = self.service._extract_data_with_llm("Mensaje", session_id)
    
    # Debe retornar dict vacío en lugar de lanzar excepción
    self.assertIsInstance(result, dict)
    self.assertEqual(len(result), 0)
```

---

### 5. test_models_extended.py
**Objetivo**: Cobertura completa de modelos (90% → 95%+)

**Incluye:**
- ✅ Tests extendidos de `Emergencia` (todos los sectores, tipos, prioridades)
- ✅ Tests extendidos de `ChatConversation` (todos los estados)
- ✅ Tests extendidos de `ChatMessage` (roles, timestamps)
- ✅ Tests de representaciones string
- ✅ Tests de campos auto-generados (timestamps, UUIDs)
- ✅ Tests de relaciones entre modelos
- ✅ Tests de cascade delete
- ✅ Tests de unicidad de campos
- ✅ Tests de QuerySets y filtros

**Tests totales: ~45**

**Ejemplo de test:**
```python
def test_emergencia_all_sectors(self):
    sectores = [
        'anibana', 'pedro_aguirre_cerda', 'villa_san_jose',
        'el_molino', 'el_laurel', 'huara', 'punta_patache'
    ]
    
    for sector in sectores:
        emergencia = Emergencia.objects.create(
            sector=sector,
            tipo_emergencia='fuga_agua',
            descripcion='Test',
            # ... otros campos
        )
        self.assertEqual(emergencia.sector, sector)
```

---

## 🚀 Cómo Ejecutar los Tests

### Ejecutar todos los tests

```bash
# Desde la raíz del proyecto Backend
python manage.py test Tests

# O con pytest
pytest Tests/
```

### Ejecutar un archivo específico

```bash
# Test del servicio de chatbot
python manage.py test Tests.test_chatbot_service

# Test del sistema RAG
python manage.py test Tests.test_rag_system

# Test de integración API
python manage.py test Tests.test_api_integration

# Test de manejo de errores
python manage.py test Tests.test_error_handling

# Test de modelos extendidos
python manage.py test Tests.test_models_extended
```

### Ejecutar con cobertura

```bash
# Generar reporte de cobertura
coverage run --source='ModuloEmergencia' manage.py test Tests
coverage report
coverage html

# Ver reporte HTML
# Abrir htmlcov/index.html en el navegador
```

### Ejecutar tests específicos

```bash
# Ejecutar una clase de tests
python manage.py test Tests.test_chatbot_service.StartConversationTests

# Ejecutar un test individual
python manage.py test Tests.test_chatbot_service.StartConversationTests.test_start_conversation_creates_new_session
```

---

## 📊 Cobertura Esperada

Después de ejecutar todos los tests, la cobertura esperada es:

| Componente | Líneas | Cobertura |
|------------|--------|-----------|
| chatbot_service.py | 534 | 75%+ |
| vector_store.py | 150 | 70%+ |
| embeddings.py | 200 | 70%+ |
| retriever.py | 180 | 70%+ |
| views.py | 300 | 75%+ |
| models.py | 120 | 95%+ |
| **TOTAL** | 1484+ | **75%+** |

---

## 🔧 Configuración de Tests

### Settings para Tests

Los tests usan la configuración de `settings.py` con algunas sobrescrituras automáticas de Django:

- Base de datos en memoria (SQLite)
- `DEBUG = True`
- Mocks para servicios externos (Gemini, ChromaDB cuando es necesario)

### Fixtures

Si necesitas datos de prueba consistentes, crea fixtures:

```bash
# Exportar datos actuales
python manage.py dumpdata ModuloEmergencia > Tests/fixtures/test_data.json

# Cargar fixtures en tests
class MyTestCase(TestCase):
    fixtures = ['test_data.json']
```

---

## 🎯 Estrategia de Testing

### 1. **Unit Tests** (Unitarios)
- Prueban funciones/métodos individuales
- Usan mocks para dependencias externas
- Rápidos de ejecutar
- Ejemplos: `test_chatbot_service.py`, `test_models_extended.py`

### 2. **Integration Tests** (Integración)
- Prueban interacción entre componentes
- Usan base de datos real (in-memory)
- Ejemplos: `test_api_integration.py`

### 3. **Edge Case Tests** (Casos Edge)
- Prueban límites y casos inusuales
- Validación de robustez
- Ejemplos: `test_error_handling.py`

---

## 🐛 Debugging Tests

### Ver output detallado

```bash
# Verbose mode
python manage.py test Tests --verbosity=2

# Con pytest, ver prints
pytest Tests/ -s

# Ver solo tests que fallan
pytest Tests/ --tb=short
```

### Ejecutar solo tests que fallaron

```bash
# Con pytest
pytest Tests/ --lf  # last-failed
pytest Tests/ --ff  # failed-first
```

---

## 📝 Guías de Testing

### Escribir Nuevos Tests

1. **Elegir el archivo correcto**:
   - Servicio de chatbot → `test_chatbot_service.py`
   - Sistema RAG → `test_rag_system.py`
   - API REST → `test_api_integration.py`
   - Errores/Edge cases → `test_error_handling.py`
   - Modelos → `test_models_extended.py`

2. **Estructura básica**:
```python
class MyFeatureTests(TestCase):
    """Tests para mi feature"""
    
    def setUp(self):
        """Preparar datos de prueba"""
        self.data = ...
    
    def test_feature_works(self):
        """Test que la feature funciona correctamente"""
        result = my_function(self.data)
        self.assertEqual(result, expected_value)
    
    def tearDown(self):
        """Limpiar después del test"""
        pass
```

3. **Usar mocks para servicios externos**:
```python
@patch('path.to.external.service')
def test_with_mock(self, mock_service):
    mock_service.return_value = "mocked response"
    result = my_function()
    self.assertEqual(result, "expected")
```

---

## 🔍 Tests Pendientes

Áreas que podrían necesitar más tests en el futuro:

- [ ] Tests de performance (tiempo de respuesta)
- [ ] Tests de carga (múltiples usuarios simultáneos)
- [ ] Tests de seguridad más exhaustivos
- [ ] Tests de UI (si se agrega interfaz web en backend)
- [ ] Tests de migración de datos
- [ ] Tests de backup/restore

---

## 📚 Referencias

- **Django Testing**: https://docs.djangoproject.com/en/5.0/topics/testing/
- **DRF Testing**: https://www.django-rest-framework.org/api-guide/testing/
- **unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **Coverage.py**: https://coverage.readthedocs.io/
- **pytest-django**: https://pytest-django.readthedocs.io/

---

## 🤝 Contribuir con Tests

Al agregar nuevas funcionalidades:

1. ✅ Escribir tests **antes** de implementar (TDD)
2. ✅ Asegurar cobertura > 70% del código nuevo
3. ✅ Incluir tests de casos edge y errores
4. ✅ Documentar tests complejos con comentarios
5. ✅ Verificar que todos los tests pasen antes de commit

---

## 📊 Reporte de Cobertura

Para generar un reporte completo:

```bash
# 1. Ejecutar tests con cobertura
coverage run --source='ModuloEmergencia' manage.py test Tests

# 2. Ver reporte en consola
coverage report

# 3. Generar reporte HTML detallado
coverage html

# 4. Ver en navegador
# Abrir htmlcov/index.html
```

El reporte mostrará:
- Líneas totales vs cubiertas
- Porcentaje de cobertura por archivo
- Líneas específicas no cubiertas (resaltadas en rojo)

---

**Última actualización**: 5 de Diciembre, 2025  
**Versión**: 1.0.0  
**Tests totales**: ~200 tests adicionales  
**Objetivo de cobertura**: 75%+ (desde 58% baseline)
