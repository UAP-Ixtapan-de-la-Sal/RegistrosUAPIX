from django.contrib import admin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    # Muestra los campos en la lista del panel de administración
    list_display = ('id', 'usuario', 'contrasena')
    
    # Opcional: Búsqueda por nombre de usuario
    search_fields = ('usuario',)