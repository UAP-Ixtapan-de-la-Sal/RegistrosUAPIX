from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone


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


# ==========================================
# === NUEVAS TABLAS PARA EL MÓDULO SALA DE CÓMPUTO ===
# ==========================================
# ==========================================
# === NUEVA TABLA: EXTERNOS (Punto 7) ===
# ==========================================
class Externo(models.Model):
    id_externo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    institucion = models.CharField(max_length=100, null=True, blank=True, verbose_name="Institución de procedencia")

    def __str__(self):
        return f"{self.nombre} {self.apellidos} (Externo)"

class Carrera(models.Model):
    id_carrera = models.AutoField(primary_key=True)
    nombre_carrera = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_carrera

class Materia(models.Model):
    id_materia = models.AutoField(primary_key=True)
    nombre_materia = models.CharField(max_length=100)
    # Reemplazamos id_carrera por carrera. Django creará la columna carrera_id automáticamente en MariaDB.
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, verbose_name="Carrera a la que pertenece")

    def __str__(self):
        return self.nombre_materia

class Grupo(models.Model):
    id_grupo = models.AutoField(primary_key=True)
    nombre_grupo = models.CharField(max_length=20)
    semestre = models.IntegerField()
    turno = models.CharField(max_length=20)
    # Misma lógica: nombre limpio para la llave foránea
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, verbose_name="Carrera")

    def __str__(self):
        return f"{self.nombre_grupo} - Semestre {self.semestre} ({self.turno})"


class Clase(models.Model):
    id_clase = models.AutoField(primary_key=True)
    
    # 1. MEJORA DE UX: Quitamos el 'id_' y ponemos etiquetas limpias
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, verbose_name="Materia")
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, verbose_name="Grupo")
    docente = models.ForeignKey(Persona, on_delete=models.CASCADE, verbose_name="Docente a cargo")
    
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    # 2. SEGURIDAD DE DATOS: Método clean() para validar las reglas de negocio
    def clean(self):
        # Evitar errores si los campos están vacíos (Django ya los valida por ser obligatorios, 
        # pero clean() corre antes, así que nos aseguramos de que tengan datos).
        if not self.fecha or not self.hora_inicio or not self.hora_fin:
            return

        # Regla A: La fecha de la clase no puede ser en el pasado
        fecha_actual = timezone.now().date()
        if self.fecha < fecha_actual:
            raise ValidationError({'fecha': 'Seguridad: No puedes agendar una clase en una fecha que ya pasó.'})

        # Regla B: Si la clase es hoy, la hora de inicio no puede haber pasado ya
        hora_actual = timezone.localtime().time()
        if self.fecha == fecha_actual and self.hora_inicio < hora_actual:
            raise ValidationError({'hora_inicio': 'Seguridad: La hora de inicio ya pasó en el día de hoy.'})

        # Regla C: La hora de fin debe ser estrictamente posterior a la de inicio
        if self.hora_fin <= self.hora_inicio:
            raise ValidationError({'hora_fin': 'Lógica: La hora de finalización debe ser después de la hora de inicio.'})

    # Sobrescribimos el método save() para forzar que clean() se ejecute siempre
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Clase: {self.materia} - {self.grupo} ({self.fecha})"

# ==========================================
# === ACTUALIZACIÓN: EVENTOS (Punto 4) ===
# ==========================================
class EventoTallerConferencia(models.Model):
    TIPO_EVENTO_CHOICES = [
        ('Taller', 'Taller'),
        ('Conferencia', 'Conferencia'),
        ('Clase', 'Clase'),
        
    ]
    TIPO_PONENTE_CHOICES = [
        ('Interno', 'Docente/Alumno del Plantel'),
        ('Externo', 'Persona Externa'),
    ]

    id_evento = models.AutoField(primary_key=True)
    # Lista desplegable para tipo de evento
    tipo_evento = models.CharField(max_length=50, choices=TIPO_EVENTO_CHOICES, default='Taller')
    nombre_evento = models.CharField(max_length=100)
    
    # Lógica de separación Interno/Externo
    tipo_ponente = models.CharField(max_length=20, choices=TIPO_PONENTE_CHOICES, default='Interno')
    ponente_interno = models.ForeignKey(Persona, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Ponente Interno")
    ponente_externo = models.ForeignKey(Externo, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Ponente Externo")
    
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    # Aclaración visual para el estado bloque
    estado_bloque = models.BooleanField("Bloquear horario", default=True, help_text="Si está activo, no se podrán asignar más actividades en este horario.")

    # Validación de seguridad y lógica de negocio
   # ==========================================
    # === SISTEMA DE SEGURIDAD Y ANTI-CHOQUES ===
    # ==========================================
    def clean(self):
        # 1. Validación Lógica Básica
        if self.hora_entrada and self.hora_salida:
            if self.hora_salida <= self.hora_entrada:
                raise ValidationError({'hora_salida': 'Error lógico: La hora de salida no puede ser antes o igual a la hora de entrada.'})

        # 2. Lógica Anti-Choque de Equipos
        if self.equipo:
            # Buscamos todos los registros del MISMO equipo en la MISMA fecha
            # .exclude(id_registro=self.id_registro) es vital por si estamos "editando" un registro, para que no choque consigo mismo.
            registros_existentes = Registro.objects.filter(
                equipo=self.equipo,
                fecha=self.fecha
            ).exclude(id_registro=self.id_registro)

            for reg in registros_existentes:
                # CASO A: Alguien está usando la computadora ahorita mismo (No ha registrado salida)
                if not reg.hora_salida:
                    raise ValidationError({'equipo': f'Bloqueo: Este equipo está siendo ocupado actualmente por alguien más (Entró a las {reg.hora_entrada}).'})

                # CASO B: Chocamos con un registro que ya terminó
                if self.hora_salida:
                    # Fórmula matemática de traslape: (Nuevo Inicio < Viejo Fin) Y (Nuevo Fin > Viejo Inicio)
                    if self.hora_entrada < reg.hora_salida and self.hora_salida > reg.hora_entrada:
                        raise ValidationError({'hora_entrada': f'Choque de horario: Este equipo ya fue utilizado de {reg.hora_entrada} a {reg.hora_salida}.'})
                else:
                    # CASO C: No le pusimos hora de salida (queda abierto), pero la entrada choca con algo previo
                    if self.hora_entrada < reg.hora_salida:
                        raise ValidationError({'hora_entrada': f'Choque de horario: La entrada interfiere con un registro previo de {reg.hora_entrada} a {reg.hora_salida}.'})

    # Automatización de estados + Ejecución del Clean
    def save(self, *args, **kwargs):
        self.full_clean() # EJECUTAMOS EL FILTRO DE SEGURIDAD ANTES DE GUARDAR
        super().save(*args, **kwargs)
        
        # Automatización de equipo
        if self.equipo:
            if self.hora_salida:
                self.equipo.estado = 'Disponible'
            else:
                self.equipo.estado = 'Ocupado'
            self.equipo.save()

    def __str__(self):
        return f"Registro {self.id_registro} - {self.modulo} ({self.fecha})"


class Equipo(models.Model):
    LUGAR_CHOICES = [
        ('Sala', 'Sala de Cómputo'),
        ('Auto Acceso', 'Auto Acceso'),
        ('Biblioteca', 'Biblioteca')
    ]
    ESTADO_CHOICES = [
        ('Disponible', 'Disponible'),
        ('Ocupado', 'Ocupado'),
        ('Mantenimiento', 'Mantenimiento'),
        ('Baja', 'Baja')
    ]
    CONDICION_CHOICES = [
        ('Bueno', 'Bueno'),
        ('Regular', 'Regular'),
        ('Malo', 'Malo')
    ]

    id_equipo = models.AutoField(primary_key=True) # MODIFICACIÓN: Clave primaria explícita según diagrama
    no_equipo = models.CharField(max_length=50)
    no_bien_patrimonial = models.CharField(max_length=100, unique=True, null=True, blank=True)
    lugar = models.CharField(max_length=50, choices=LUGAR_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Disponible')
    condicion = models.CharField(max_length=20, choices=CONDICION_CHOICES, default='Bueno')
    observaciones = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Eq: {self.no_equipo} ({self.lugar})"


class Registro(models.Model):
    MODULO_CHOICES = [
        ('Sala_Computo', 'Sala de Cómputo'),
        ('Auto_Acceso', 'Auto Acceso'),
        ('Biblioteca', 'Biblioteca Digital')
    ]
    TIPO_REGISTRO_CHOICES = [
        ('Clase', 'Clase'),
        ('Evento', 'Evento'),
        ('Visita', 'Visita')
    ]
    MOTIVO_USO_CHOICES = [
        ('Clase', 'Clase'),
        ('Visita', 'Visita'),
        ('Conversacion', 'Conversación')
    ]

    id_registro = models.AutoField(primary_key=True)
    modulo = models.CharField(max_length=20, choices=MODULO_CHOICES, default='Sala_Computo')
    tipo_registro = models.CharField(max_length=20, choices=TIPO_REGISTRO_CHOICES, null=True, blank=True)
    motivo_uso = models.CharField(max_length=20, choices=MOTIVO_USO_CHOICES, null=True, blank=True)
    
    fecha = models.DateField(default=timezone.now)
    hora_entrada = models.TimeField(default=timezone.now)
    hora_salida = models.TimeField(null=True, blank=True)
    
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, verbose_name="Usuario / Persona")
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Equipo de Cómputo")
    clase = models.ForeignKey(Clase, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Clase asignada")
    evento = models.ForeignKey(EventoTallerConferencia, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Evento asignado")
    registrado_por = models.ForeignKey(UsuarioSistema, on_delete=models.SET_NULL, null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)

    # MODIFICACIÓN PUNTO 3: Automatización del estado del equipo
    def save(self, *args, **kwargs):
        # Primero guardamos el registro para asegurarnos de que existe
        super().save(*args, **kwargs)
        
        # Si este registro tiene una computadora asignada...
        if self.equipo:
            if self.hora_salida:
                # Si ya le pusieron hora de salida, liberamos la PC
                self.equipo.estado = 'Disponible'
            else:
                # Si no tiene hora de salida, significa que la acaban de ocupar
                self.equipo.estado = 'Ocupado'
            
            # Guardamos el nuevo estado de la computadora
            self.equipo.save()

    def __str__(self):
        return f"Registro {self.id_registro} - {self.modulo} ({self.fecha})"