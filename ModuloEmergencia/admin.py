from django.contrib import admin
from .models import Emergencia, ChatConversation, ChatMessage


@admin.register(Emergencia)
class EmergenciaAdmin(admin.ModelAdmin):
    list_display = ('id_emergencia', 'nombre_usuario', 'telefono', 'sector', 
                    'tipo_emergencia', 'nivel_prioridad', 'estado_emergencia', 'fecha_creacion')
    list_filter = ('estado_emergencia', 'tipo_emergencia', 'nivel_prioridad', 'sector')
    search_fields = ('nombre_usuario', 'telefono', 'descripcion', 'direccion')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('id_emergencia', 'fecha_creacion', 'fecha_actualizacion')


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_id', 'estado', 'fecha_inicio', 'emergencia')
    list_filter = ('estado', 'fecha_inicio')
    search_fields = ('session_id',)
    ordering = ('-fecha_inicio',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'rol', 'timestamp')
    list_filter = ('rol', 'timestamp')
    ordering = ('-timestamp',)
