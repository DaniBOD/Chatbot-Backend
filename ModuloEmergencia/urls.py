"""
URLs para el módulo de emergencias
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'emergencias', views.EmergenciaViewSet, basename='emergencia')
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
