from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioSistema, Persona

@admin.register(UsuarioSistema)
class UsuarioSistemaAdmin(UserAdmin):
    # 1. Las columnas que verás en la tabla principal del panel
    list_display = ('username', 'rol', 'mod_sala_computo', 'mod_prestamos', 'is_superuser')
    
    # 2. Filtros para buscar usuarios rápidamente por rol
    list_filter = ('rol', 'is_superuser')

    # 3. Esto es clave: Agrega tus checkboxes a la pantalla de editar usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Configuración de Roles y Módulos UAPIX', {
            'fields': (
                'rol', 
                'mod_sala_computo', 
                'mod_auto_acceso', 
                'mod_biblioteca', 
                'mod_prestamos', 
                'mod_insumos', 
                'mod_tecnologicos'
            )
        }),
    )

# Dejamos la tabla Persona lista por si quieren ir agregando alumnos manuales después
@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'nombre', 'apellidos', 'perfil')
    search_fields = ('matricula', 'nombre', 'apellidos')