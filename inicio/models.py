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