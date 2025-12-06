import requests
import json

print("=== Probando Backend del Chatbot ===\n")

# 1. Iniciar conversación
print("1️⃣ Iniciando conversación...")
response = requests.post(
    "http://localhost:8000/api/emergencias/chat/init/",
    json={}
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")

session_id = data.get('session_id')
print(f"\n✅ Session ID: {session_id}\n")

# 2. Enviar mensaje
print("2️⃣ Enviando mensaje...")
response = requests.post(
    "http://localhost:8000/api/emergencias/chat/message/",
    json={
        "session_id": session_id,
        "message": "Hola, tengo una emergencia de agua en mi casa"
    }
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Bot: {data.get('response')}")
print(f"Estado: {data.get('estado')}\n")

# 3. Segundo mensaje
print("3️⃣ Segundo mensaje...")
response = requests.post(
    "http://localhost:8000/api/emergencias/chat/message/",
    json={
        "session_id": session_id,
        "message": "Sector Pedro Aguirre Cerda"
    }
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Bot: {data.get('response')}")
print(f"Estado: {data.get('estado')}\n")

print("✅ ¡Prueba completada!")
