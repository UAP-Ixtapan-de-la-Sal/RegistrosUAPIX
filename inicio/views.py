from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import UsuarioSistema
from .forms import RegistroUsuarioForm

# 1. VISTA DE LOGIN
def login_view(request):
    if request.method == 'POST':
        username_ingresado = request.POST.get('usuario')
        password_ingresado = request.POST.get('contrasena')
        
        user = authenticate(request, username=username_ingresado, password=password_ingresado)
        
        if user is not None:
            login(request, user)
            
            # Inicializamos el sello de tiempo estricto para el administrador
            request.session['ultima_actividad'] = datetime.now().timestamp()
            request.session.pop('admin_reautenticado', None)
            request.session.modified = True
            
            return redirect('homePage')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            
    return render(request, 'inicio/login.html')

# 2. VISTA DEL HOMEPAGE (Con control de inactividad de 1 min solo para superusuario)
@login_required
def homePage(request):
    if request.user.is_superuser:
        ahora = datetime.now().timestamp()
        
        # Si no existe un registro previo, lo inicializamos
        if 'ultima_actividad' not in request.session:
            request.session['ultima_actividad'] = ahora
            request.session.modified = True
            
        ultima_actividad = request.session.get('ultima_actividad')
        
        # Evaluamos si han pasado más de 10 segundos (10 segundos)
        if (ahora - ultima_actividad) > 10:
            logout(request)
            messages.error(request, "Sesión de administrador cerrada por inactividad de seguridad.")
            return redirect('login')
            
        # Actualizamos la marca de tiempo solo si el usuario interactúa explícitamente
        request.session['ultima_actividad'] = ahora
        request.session.modified = True
        
    # Los operadores comunes trabajan todo el día sin restricciones
    return render(request, 'inicio/homePage.html')

# 3. CANDADO DE SEGURIDAD
def es_admin_general(user):
    return user.is_superuser

# 4. VISTA PARA AGREGAR USUARIO
@login_required
@user_passes_test(es_admin_general, login_url='homePage')
def agregar_usuario_view(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        
        if form.is_valid():
            form.save() 
            messages.success(request, "¡Usuario y Permisos Guardados Exitosamente!")
            return redirect('agregar_usuario')
        else:
            messages.error(request, "Error al crear el usuario. Verifica los datos ingresados.")
    else:
        form = RegistroUsuarioForm()

    return render(request, 'inicio/agregar_usuario.html', {'form': form})

# 5. VISTA DE LOGOUT
def logout_view(request):
    logout(request)
    return redirect('login')

#6. VISTA DE AUDITORÍA Y REPORTES
@login_required
def auditoria_reportes_view(request):
    # Lógica para la vista de auditoría y reportes
    return render(request, 'inicio/auditoria_reportes.html')

#7. VISTA DE RESPALDOS DE BASE DE DATOS
@login_required
def respaldos_bd_view(request):
    # Lógica para la vista de respaldos de base de datos
    return render(request, 'inicio/respaldos_bd.html')