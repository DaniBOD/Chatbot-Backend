from django.db import models
from django.core.validators import RegexValidator
import uuid


class Emergencia(models.Model):
    """
    Modelo para registrar emergencias reportadas por los usuarios.
    Basado en el diagrama de base de datos de emergencias.
    """
    
    SECTORES = [
        ('anibana', 'Anibana'),
        ('el_molino', 'El Molino'),
        ('la_compania', 'La Compañía'),
        ('el_maiten_1', 'El Maitén 1'),
        ('la_morera', 'La Morera'),
        ('el_maiten_2', 'El Maitén 2'),
        ('santa_margarita', 'Santa Margarita'),
    ]
    
    TIPOS_EMERGENCIA = [
        ('rotura_matriz', 'Rotura de Matriz'),
        ('baja_presion', 'Baja Presión'),
        ('fuga_agua', 'Fuga de Agua'),
        ('caneria_rota', 'Cañería Rota'),
        ('agua_contaminada', 'Agua Contaminada'),
        ('sin_agua', 'Sin Agua'),
        ('otro', 'Otro'),
    ]
    
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('atendida', 'Atendida'),
        ('resuelta', 'Resuelta'),
        ('cancelada', 'Cancelada'),
    ]
    
    NIVELES_PRIORIDAD = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    # PK según diagrama
    id_emergencia = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID Emergencia'
    )
    
    # Datos del usuario (X1, X3, X4, X6, X7)
    nombre_usuario = models.CharField(
        max_length=200,
        verbose_name='Nombre del Usuario'
    )
    
    telefono_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Número de teléfono debe tener entre 9 y 15 dígitos."
    )
    telefono = models.CharField(
        validators=[telefono_validator],
        max_length=17,
        verbose_name='Teléfono'
    )
    
    sector = models.CharField(
        max_length=50,
        choices=SECTORES,
        verbose_name='Sector'
    )
    
    direccion = models.CharField(
        max_length=500,
        verbose_name='Dirección'
    )
    
    # Datos de la emergencia (X2, X5)
    descripcion = models.TextField(
        verbose_name='Descripción de la Emergencia'
    )
    
    tipo_emergencia = models.CharField(
        max_length=50,
        choices=TIPOS_EMERGENCIA,
        verbose_name='Tipo de Emergencia'
    )
    
    # Datos adicionales recolectados
    medidor_corriendo = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='¿Medidor Corriendo?',
        help_text='Indica si el medidor está corriendo'
    )
    
    cantidad_agua = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Cantidad de Agua (Fuga)',
        help_text='Descripción de la cantidad de agua en caso de fuga'
    )
    
    fotografia = models.ImageField(
        upload_to='emergencias/fotos/',
        null=True,
        blank=True,
        verbose_name='Fotografía (Opcional)'
    )
    
    # Estado y prioridad
    estado_emergencia = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente',
        verbose_name='Estado de la Emergencia'
    )
    
    nivel_prioridad = models.CharField(
        max_length=20,
        choices=NIVELES_PRIORIDAD,
        default='media',
        verbose_name='Nivel de Prioridad'
    )
    
    # Contacto colaborativo
    solicita_contacto_colaborativo = models.BooleanField(
        default=False,
        verbose_name='Solicita Datos de Contacto Colaborativo'
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    # Notas internas
    notas_internas = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notas Internas',
        help_text='Notas del personal operativo'
    )
    
    class Meta:
        verbose_name = 'Emergencia'
        verbose_name_plural = 'Emergencias'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['-fecha_creacion']),
            models.Index(fields=['estado_emergencia']),
            models.Index(fields=['sector']),
            models.Index(fields=['nivel_prioridad']),
        ]
    
    def __str__(self):
        return f"Emergencia {self.id_emergencia} - {self.nombre_usuario} ({self.sector})"
    
    def calcular_prioridad(self):
        """
        Calcula el nivel de prioridad basado en el tipo de emergencia
        y otros factores según el flujo del chatbot.
        """
        prioridad_map = {
            'rotura_matriz': 'critica',
            'sin_agua': 'critica',
            'agua_contaminada': 'alta',
            'caneria_rota': 'alta',
            'fuga_agua': 'media',
            'baja_presion': 'media',
            'otro': 'baja',
        }
        
        prioridad_base = prioridad_map.get(self.tipo_emergencia, 'media')
        
        # Ajustar según medidor corriendo (mayor fuga)
        if self.medidor_corriendo and prioridad_base in ['media', 'baja']:
            if prioridad_base == 'media':
                prioridad_base = 'alta'
            elif prioridad_base == 'baja':
                prioridad_base = 'media'
        
        self.nivel_prioridad = prioridad_base
        return prioridad_base


class ChatConversation(models.Model):
    """
    Modelo para gestionar conversaciones de chat.
    Mantiene el estado de la conversación con el usuario.
    """
    
    ESTADOS_CONVERSACION = [
        ('iniciada', 'Iniciada'),
        ('recolectando_datos', 'Recolectando Datos'),
        ('calculando_prioridad', 'Calculando Prioridad'),
        ('solicitando_contacto', 'Solicitando Contacto'),
        ('finalizada', 'Finalizada'),
        ('abandonada', 'Abandonada'),
    ]
    
    session_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='ID de Sesión'
    )
    
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS_CONVERSACION,
        default='iniciada',
        verbose_name='Estado de la Conversación'
    )
    
    # Datos recolectados durante la conversación (temporal)
    datos_recolectados = models.JSONField(
        default=dict,
        verbose_name='Datos Recolectados',
        help_text='Almacena los datos X1-X7 mientras se recolectan'
    )
    
    # Relación con emergencia creada
    emergencia = models.OneToOneField(
        Emergencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversacion',
        verbose_name='Emergencia Asociada'
    )
    
    # Timestamps
    fecha_inicio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Inicio'
    )
    
    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Fin'
    )
    
    class Meta:
        verbose_name = 'Conversación de Chat'
        verbose_name_plural = 'Conversaciones de Chat'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Conversación {self.session_id} - {self.estado}"


class ChatMessage(models.Model):
    """
    Modelo para almacenar mensajes individuales del chat.
    """
    
    ROLES = [
        ('usuario', 'Usuario'),
        ('asistente', 'Asistente'),
        ('sistema', 'Sistema'),
    ]
    
    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='mensajes',
        verbose_name='Conversación'
    )
    
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        verbose_name='Rol'
    )
    
    contenido = models.TextField(
        verbose_name='Contenido del Mensaje'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y Hora'
    )
    
    # Metadata adicional
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadatos',
        help_text='Información adicional del mensaje'
    )
    
    class Meta:
        verbose_name = 'Mensaje de Chat'
        verbose_name_plural = 'Mensajes de Chat'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.rol} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
