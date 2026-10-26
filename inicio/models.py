from django.db import models
from django.contrib.auth.models import AbstractUser

class UsuarioSistema(AbstractUser):
    # 1. Definimos el Rol (Operador o Visualizador)
    ROLES = (
        ('operador', 'Operador de Módulo'),
        ('visualizador', 'Visualizador'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='visualizador')

    # 2. Reemplazamos los permisos del 'class Meta' por checkboxes reales
    mod_sala_computo = models.BooleanField('Sala de Cómputo', default=False)
    mod_auto_acceso = models.BooleanField('Auto Acceso', default=False)
    mod_biblioteca = models.BooleanField('Biblioteca Digital', default=False)
    mod_prestamos = models.BooleanField('Préstamos y Devolución', default=False)
    mod_insumos = models.BooleanField('Control de Insumos', default=False)
    mod_tecnologicos = models.BooleanField('Insumos Tecnológicos', default=False)

    def __str__(self):
        return self.username

class Persona(models.Model):
    id_persona = models.AutoField(primary_key=True)
    id_carrera = models.IntegerField(null=True, blank=True)
    perfil = models.CharField(max_length=50, choices=[
        ('Admin', 'Admin'),
        ('Doc', 'Doc'),
        ('Alumno', 'Alumno'),
        ('Ext', 'Ext')
    ])
    matricula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.matricula or 'S/N'} {self.nombre} {self.apellidos}"


class RegistroActividadSala(models.Model):
    CATEGORIA_CLASE = 'clase'
    CATEGORIA_EVENTO = 'evento'
    CATEGORIAS = (
        (CATEGORIA_CLASE, 'Clase'),
        (CATEGORIA_EVENTO, 'Evento'),
    )
    TIPOS_ACTIVIDAD = (
        ('regular', 'Clase regular'),
        ('taller', 'Taller'),
        ('conferencia', 'Conferencia'),
        ('clase', 'Clase'),
    )

    categoria = models.CharField(max_length=10, choices=CATEGORIAS)
    tipo_actividad = models.CharField(max_length=20, choices=TIPOS_ACTIVIDAD)
    pertenece_al_plantel = models.BooleanField(null=True, blank=True)
    nombre_actividad = models.CharField(max_length=150)
    responsable = models.CharField(max_length=150)
    numero_cuenta_docente = models.CharField(max_length=20, blank=True)
    serie_recurrente = models.UUIDField(null=True, blank=True, db_index=True)
    grupo = models.CharField(max_length=30, blank=True)
    materia = models.CharField(max_length=150, blank=True)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    creado_por = models.ForeignKey(
        'inicio.UsuarioSistema',
        on_delete=models.PROTECT,
        related_name='actividades_sala',
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('fecha', 'hora_inicio')
        verbose_name = 'registro de actividad de sala'
        verbose_name_plural = 'registros de actividades de sala'

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.hora_inicio and self.hora_fin and self.hora_fin <= self.hora_inicio:
            raise ValidationError({'hora_fin': 'La hora de término debe ser posterior a la hora de inicio.'})

        if self.categoria == self.CATEGORIA_CLASE:
            if not self.grupo or not self.materia or not self.numero_cuenta_docente:
                raise ValidationError('Las clases requieren docente, grupo y materia.')
            if self.pertenece_al_plantel is not None:
                raise ValidationError({'pertenece_al_plantel': 'Este dato solo aplica para eventos.'})
        elif self.categoria == self.CATEGORIA_EVENTO:
            if self.pertenece_al_plantel is None:
                raise ValidationError({'pertenece_al_plantel': 'Indica si la persona pertenece al plantel.'})
            if self.grupo or self.materia:
                raise ValidationError('Los eventos no deben incluir grupo ni materia.')

    def __str__(self):
        return f'{self.get_categoria_display()}: {self.nombre_actividad} ({self.fecha})'