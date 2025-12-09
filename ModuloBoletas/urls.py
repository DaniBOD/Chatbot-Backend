"""
URLs para el módulo de boletas
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Router para ViewSets
router = DefaultRouter()
# Registrar el ViewSet de boletas en la raíz del módulo para que las rutas sean:
#  - /api/boletas/       -> list/create
#  - /api/boletas/consultar/ -> action consultar
router.register(r'', views.BoletaViewSet, basename='boleta')
router.register(r'conversaciones', views.ChatConversationViewSet, basename='conversacion')

# URLs del módulo
urlpatterns = [
    # Endpoints del router
    path('', include(router.urls)),
    
    # Endpoints de chat
    path('chat/init/', views.init_chat, name='chat-init'),
    path('chat/message/', views.chat_message, name='chat-message'),
    path('chat/status/<str:session_id>/', views.chat_status, name='chat-status'),
    
    # Endpoint de estadísticas RAG
    path('rag/stats/', views.rag_stats, name='rag-stats'),
]
