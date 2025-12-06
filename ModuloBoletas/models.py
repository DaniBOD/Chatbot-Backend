"""
Modelos para el módulo de boletas.
Gestiona boletas de consumo de agua y conversaciones de chat para consultas.
"""
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import uuid


def validar_rut_chileno(rut):
    """
    Valida el formato básico de un RUT chileno (XX.XXX.XXX-X o XXXXXXXX-X)
    """
    import re
    # Permitir formato con o sin puntos
    pattern = r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$|^\d{7,8}-[\dkK]$'
    if not re.match(pattern, rut):
        raise ValidationError('RUT debe estar en formato XX.XXX.XXX-X o XXXXXXXX-X')


class Boleta(models.Model):
    """
    Modelo para registrar boletas de consumo de agua.
    Basado en el diagrama de flujo de consultas de boletas.
    
    Campos principales:
    - id_boleta: Identificador único de la boleta
    - fecha_emision: Fecha de emisión de la boleta
    - nombre: Nombre del cliente
    - rut: RUT del cliente
    - direccion: Dirección del cliente
    - monto: Monto total a pagar
    - consumo: Consumo en metros cúbicos
    """
    
    # PK según diagrama
    id_boleta = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID Boleta'
    )
    
    # Datos del cliente (según diagrama: nombre, rut, direccion)
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Cliente',
        help_text='Nombre completo del cliente'
    )
    
    rut = models.CharField(
        max_length=12,
        validators=[validar_rut_chileno],
        verbose_name='RUT',
        help_text='RUT en formato XX.XXX.XXX-X',
        db_index=True
    )
    
    direccion = models.CharField(
        max_length=500,
        verbose_name='Dirección',
        help_text='Dirección del domicilio'
    )
    
    # Datos de la boleta (según diagrama: fecha_emision, monto, consumo)
    fecha_emision = models.DateField(
        verbose_name='Fecha de Emisión',
        help_text='Fecha de emisión de la boleta',
        db_index=True
    )
    
    periodo_facturacion = models.CharField(
        max_length=20,
        verbose_name='Período de Facturación',
        help_text='Ejemplo: 2025-11, 2025-12',
        blank=True
    )
    
    consumo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Consumo (m³)',
        help_text='Consumo en metros cúbicos'
    )
    
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Monto Total',
        help_text='Monto total a pagar en pesos chilenos'
    )
    
    # Datos adicionales
    lectura_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Lectura Anterior (m³)',
        help_text='Lectura del medidor del período anterior'
    )
    
    lectura_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Lectura Actual (m³)',
        help_text='Lectura del medidor actual'
    )
    
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Vencimiento',
        help_text='Fecha límite de pago'
    )
    
    estado_pago = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('pagada', 'Pagada'),
            ('vencida', 'Vencida'),
            ('anulada', 'Anulada'),
        ],
        default='pendiente',
        verbose_name='Estado de Pago'
    )
    
    # Imagen de la boleta (opcional)
    imagen_boleta = models.ImageField(
        upload_to='boletas/imagenes/',
        null=True,
        blank=True,
        verbose_name='Imagen de la Boleta',
        help_text='Imagen escaneada o fotografía de la boleta'
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación en Sistema'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    # Notas internas
    notas = models.TextField(
        blank=True,
        verbose_name='Notas',
        help_text='Notas adicionales sobre la boleta'
    )
    
    class Meta:
        verbose_name = 'Boleta'
        verbose_name_plural = 'Boletas'
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['-fecha_emision']),
            models.Index(fields=['rut']),
            models.Index(fields=['estado_pago']),
            models.Index(fields=['periodo_facturacion']),
        ]
        unique_together = [['rut', 'periodo_facturacion']]
    
    def __str__(self):
        return f"Boleta {self.periodo_facturacion} - {self.nombre} ({self.rut})"
    
    def calcular_consumo(self):
        """
        Calcula el consumo basado en lecturas si están disponibles
        """
        if self.lectura_anterior is not None and self.lectura_actual is not None:
            self.consumo = self.lectura_actual - self.lectura_anterior
        return self.consumo
    
    def get_consumo_promedio_diario(self):
        """
        Calcula el consumo promedio diario (asumiendo 30 días)
        """
        return float(self.consumo) / 30 if self.consumo else 0
    
    def esta_vencida(self):
        """
        Verifica si la boleta está vencida
        """
        from django.utils import timezone
        if self.fecha_vencimiento:
            return timezone.now().date() > self.fecha_vencimiento
        return False


class ChatConversation(models.Model):
    """
    Modelo para gestionar conversaciones de chat sobre boletas.
    Mantiene el estado de la conversación con el usuario.
    
    Flujo según diagrama:
    1. iniciada: Conversación recién iniciada
    2. recolectando_datos: Preguntando motivo y verificando boleta
    3. consultando: Respondiendo preguntas sobre boleta
    4. finalizada: Conversación terminada
    """
    
    ESTADOS_CONVERSACION = [
        ('iniciada', 'Iniciada'),
        ('recolectando_datos', 'Recolectando Datos'),
        ('consultando', 'Consultando'),
        ('comparando', 'Comparando Boletas'),
        ('finalizada', 'Finalizada'),
        ('abandonada', 'Abandonada'),
    ]
    
    session_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='ID de Sesión',
        db_index=True
    )
    
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS_CONVERSACION,
        default='iniciada',
        verbose_name='Estado de la Conversación'
    )
    
    # Datos recolectados durante la conversación
    datos_recolectados = models.JSONField(
        default=dict,
        verbose_name='Datos Recolectados',
        help_text='Almacena RUT, motivo de consulta, etc.'
    )
    
    # Relación con boleta(s) consultada(s)
    boleta_principal = models.ForeignKey(
        Boleta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversaciones',
        verbose_name='Boleta Principal'
    )
    
    # Para consultas comparativas
    boletas_comparadas = models.ManyToManyField(
        Boleta,
        blank=True,
        related_name='conversaciones_comparativas',
        verbose_name='Boletas Comparadas',
        help_text='Boletas involucradas en consultas comparativas'
    )
    
    # Indica si la consulta es comparativa
    es_consulta_comparativa = models.BooleanField(
        default=False,
        verbose_name='¿Es Consulta Comparativa?',
        help_text='Indica si el usuario está comparando boletas'
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
    
    # Metadata adicional
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadatos',
        help_text='Información adicional de la conversación'
    )
    
    class Meta:
        verbose_name = 'Conversación de Chat'
        verbose_name_plural = 'Conversaciones de Chat'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['-fecha_inicio']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"Conversación {self.session_id} - {self.estado}"
    
    def finalizar(self):
        """
        Finaliza la conversación
        """
        from django.utils import timezone
        self.estado = 'finalizada'
        self.fecha_fin = timezone.now()
        self.save()


class ChatMessage(models.Model):
    """
    Modelo para almacenar mensajes individuales del chat.
    Registra cada interacción entre el usuario y el asistente.
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
        verbose_name='Fecha y Hora',
        db_index=True
    )
    
    # Metadata adicional
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadatos',
        help_text='Información adicional del mensaje (intenciones detectadas, contexto RAG, etc.)'
    )
    
    class Meta:
        verbose_name = 'Mensaje de Chat'
        verbose_name_plural = 'Mensajes de Chat'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        preview = self.contenido[:50] + '...' if len(self.contenido) > 50 else self.contenido
        return f"{self.rol} - {self.timestamp.strftime('%Y-%m-%d %H:%M')} - {preview}"
