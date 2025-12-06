"""
Configuración del admin de Django para el módulo de boletas
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from .models import Boleta, ChatConversation, ChatMessage


@admin.register(Boleta)
class BoletaAdmin(admin.ModelAdmin):
    """
    Administración de boletas con filtros, búsqueda y acciones personalizadas
    """
    list_display = ('id_boleta_corto', 'nombre', 'rut',
                    'periodo_facturacion', 'consumo', 'monto',
                    'estado_pago_badge', 'esta_vencida_badge', 'fecha_emision', 'fecha_vencimiento'
    )
    
    list_filter = ( 'estado_pago', 'fecha_emision',
                    'fecha_vencimiento', 'periodo_facturacion',
    )
    
    search_fields = ('nombre', 'rut',
                     'direccion', 'periodo_facturacion',
                     'id_boleta'
    )
    
    ordering = ('-fecha_emision', '-periodo_facturacion')
    
    readonly_fields = (
        'id_boleta',
        'fecha_creacion',
        'fecha_actualizacion',
        'consumo_promedio_diario_display',
        'esta_vencida_display'
    )
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre', 'rut', 'direccion')
        }),
        ('Información de la Boleta', {
            'fields': (
                'id_boleta',
                'periodo_facturacion',
                'fecha_emision',
                'fecha_vencimiento',
                'estado_pago'
            )
        }),
        ('Consumo y Monto', {
            'fields': (
                'consumo',
                'monto',
                'lecturas',
                'consumo_promedio_diario_display'
            )
        }),
        ('Imagen', {
            'fields': ('imagen_boleta',),
            'classes': ('collapse',)
        }),
        ('Notas Adicionales', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'esta_vencida_display'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'marcar_como_pagada',
        'marcar_como_vencida',
        'calcular_consumos',
        'exportar_seleccionadas'
    ]
    
    list_per_page = 25
    date_hierarchy = 'fecha_emision'
    
    def id_boleta_corto(self, obj):
        """Muestra los primeros 8 caracteres del UUID"""
        return str(obj.id_boleta)[:8] + '...'
    id_boleta_corto.short_description = 'ID'
    
    def estado_pago_badge(self, obj):
        """Muestra el estado de pago con color"""
        colors = {
            'pendiente': 'orange',
            'pagada': 'green',
            'vencida': 'red',
            'anulada': 'gray'
        }
        color = colors.get(obj.estado_pago, 'black')
        return format_html(
            '<span style="padding: 3px 8px; background-color: {}; color: white; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_pago_display()
        )
    estado_pago_badge.short_description = 'Estado'
    
    def esta_vencida_badge(self, obj):
        """Muestra si la boleta está vencida"""
        if obj.esta_vencida():
            return format_html(
                '<span style="padding: 3px 8px; background-color: red; color: white; border-radius: 3px;">⚠ VENCIDA</span>'
            )
        return format_html(
            '<span style="padding: 3px 8px; background-color: green; color: white; border-radius: 3px;">✓ Vigente</span>'
        )
    esta_vencida_badge.short_description = 'Vencimiento'
    
    def consumo_promedio_diario_display(self, obj):
        """Muestra el consumo promedio diario"""
        promedio = obj.get_consumo_promedio_diario()
        return f"{promedio} m³/día" if promedio else "N/A"
    consumo_promedio_diario_display.short_description = 'Consumo Promedio Diario'
    
    def esta_vencida_display(self, obj):
        """Muestra si está vencida (para fieldsets)"""
        return "Sí" if obj.esta_vencida() else "No"
    esta_vencida_display.short_description = '¿Está vencida?'
    
    @admin.action(description='Marcar como pagada')
    def marcar_como_pagada(self, request, queryset):
        """Marca las boletas seleccionadas como pagadas"""
        updated = queryset.update(estado_pago='pagada')
        self.message_user(request, f'{updated} boleta(s) marcada(s) como pagada(s).')
    
    @admin.action(description='Marcar como vencida')
    def marcar_como_vencida(self, request, queryset):
        """Marca las boletas seleccionadas como vencidas"""
        updated = queryset.update(estado_pago='vencida')
        self.message_user(request, f'{updated} boleta(s) marcada(s) como vencida(s).')
    
    @admin.action(description='Calcular consumos')
    def calcular_consumos(self, request, queryset):
        """Recalcula el consumo de las boletas seleccionadas basado en lecturas"""
        count = 0
        for boleta in queryset:
            consumo_calculado = boleta.calcular_consumo()
            if consumo_calculado is not None:
                boleta.consumo = consumo_calculado
                boleta.save()
                count += 1
        self.message_user(request, f'Consumo recalculado para {count} boleta(s).')
    
    @admin.action(description='Exportar seleccionadas (CSV)')
    def exportar_seleccionadas(self, request, queryset):
        """Exporta las boletas seleccionadas a CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="boletas_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Nombre', 'RUT', 'Período', 'Fecha Emisión',
            'Fecha Vencimiento', 'Consumo (m³)', 'Monto', 'Estado Pago'
        ])
        
        for boleta in queryset:
            writer.writerow([
                str(boleta.id_boleta),
                boleta.nombre,
                boleta.rut,
                boleta.periodo_facturacion,
                boleta.fecha_emision,
                boleta.fecha_vencimiento,
                boleta.consumo,
                boleta.monto,
                boleta.get_estado_pago_display()
            ])
        
        return response
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        qs = super().get_queryset(request)
        return qs.select_related()


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    """
    Administración de conversaciones de chat
    """
    list_display = (
        'session_id_corto',
        'estado_badge',
        'es_consulta_comparativa',
        'cantidad_mensajes',
        'boleta_principal',
        'cantidad_boletas_comparadas',
        'fecha_inicio',
        'fecha_fin'
    )
    
    list_filter = (
        'estado',
        'es_consulta_comparativa',
        'fecha_inicio',
    )
    
    search_fields = (
        'session_id',
    )
    
    ordering = ('-fecha_inicio',)
    
    readonly_fields = (
        'session_id',
        'fecha_inicio',
        'fecha_fin',
        'cantidad_mensajes',
        'cantidad_boletas_comparadas'
    )
    
    fieldsets = (
        ('Información de la Conversación', {
            'fields': ('session_id', 'estado', 'es_consulta_comparativa')
        }),
        ('Boletas Relacionadas', {
            'fields': ('boleta_principal', 'boletas_comparadas')
        }),
        ('Datos Recolectados', {
            'fields': ('datos_recolectados',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'cantidad_mensajes',
                'cantidad_boletas_comparadas',
                'fecha_inicio',
                'fecha_fin',
                'metadata'
            ),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('boletas_comparadas',)
    
    actions = ['finalizar_conversaciones', 'marcar_como_abandonadas']
    
    list_per_page = 25
    date_hierarchy = 'fecha_inicio'
    
    def session_id_corto(self, obj):
        """Muestra los primeros 8 caracteres del session_id"""
        return str(obj.session_id)[:8] + '...'
    session_id_corto.short_description = 'Session ID'
    
    def estado_badge(self, obj):
        """Muestra el estado con color"""
        colors = {
            'iniciada': 'blue',
            'recolectando_datos': 'orange',
            'consultando': 'purple',
            'comparando': 'cyan',
            'finalizada': 'green',
            'abandonada': 'gray'
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="padding: 3px 8px; background-color: {}; color: white; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def cantidad_mensajes(self, obj):
        """Cuenta los mensajes de la conversación"""
        return obj.mensajes.count()
    cantidad_mensajes.short_description = 'Mensajes'
    
    def cantidad_boletas_comparadas(self, obj):
        """Cuenta las boletas comparadas"""
        return obj.boletas_comparadas.count()
    cantidad_boletas_comparadas.short_description = 'Boletas Comparadas'
    
    @admin.action(description='Finalizar conversaciones')
    def finalizar_conversaciones(self, request, queryset):
        """Finaliza las conversaciones seleccionadas"""
        count = 0
        for conversation in queryset:
            if conversation.estado not in ['finalizada', 'abandonada']:
                conversation.finalizar()
                count += 1
        self.message_user(request, f'{count} conversación(es) finalizada(s).')
    
    @admin.action(description='Marcar como abandonadas')
    def marcar_como_abandonadas(self, request, queryset):
        """Marca las conversaciones como abandonadas"""
        updated = queryset.exclude(
            estado__in=['finalizada', 'abandonada']
        ).update(estado='abandonada')
        self.message_user(request, f'{updated} conversación(es) marcada(s) como abandonada(s).')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """
    Administración de mensajes de chat
    """
    list_display = (
        'id',
        'conversation_session_id',
        'rol_badge',
        'contenido_corto',
        'timestamp'
    )
    
    list_filter = (
        'rol',
        'timestamp',
    )
    
    search_fields = (
        'contenido',
        'conversation__session_id'
    )
    
    ordering = ('-timestamp',)
    
    readonly_fields = (
        'conversation',
        'timestamp'
    )
    
    fieldsets = (
        ('Mensaje', {
            'fields': ('conversation', 'rol', 'contenido')
        }),
        ('Metadatos', {
            'fields': ('timestamp', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'timestamp'
    
    def conversation_session_id(self, obj):
        """Muestra el session_id de la conversación"""
        return str(obj.conversation.session_id)[:8] + '...'
    conversation_session_id.short_description = 'Conversación'
    
    def rol_badge(self, obj):
        """Muestra el rol con color"""
        colors = {
            'usuario': 'blue',
            'asistente': 'green',
            'sistema': 'gray'
        }
        color = colors.get(obj.rol, 'black')
        icons = {
            'usuario': '👤',
            'asistente': '🤖',
            'sistema': '⚙️'
        }
        icon = icons.get(obj.rol, '')
        return format_html(
            '<span style="padding: 3px 8px; background-color: {}; color: white; border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_rol_display()
        )
    rol_badge.short_description = 'Rol'
    
    def contenido_corto(self, obj):
        """Muestra los primeros 50 caracteres del contenido"""
        if len(obj.contenido) > 50:
            return obj.contenido[:50] + '...'
        return obj.contenido
    contenido_corto.short_description = 'Contenido'
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        qs = super().get_queryset(request)
        return qs.select_related('conversation')


# Configuración del sitio de administración
admin.site.site_header = "Administración - Módulo de Boletas"
admin.site.site_title = "Admin Boletas"
admin.site.index_title = "Gestión de Boletas y Conversaciones"
