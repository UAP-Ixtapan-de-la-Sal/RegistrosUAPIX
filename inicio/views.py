from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import UsuarioSistema
from .forms import RegistroUsuarioForm  # Importamos tu nuevo escudo de seguridad

# 1. VISTA DE LOGIN (Se mantiene tu código exacto)
def login_view(request):
    if request.method == 'POST':
        username_ingresado = request.POST.get('usuario')
        password_ingresado = request.POST.get('contrasena')
        
        user = authenticate(request, username=username_ingresado, password=password_ingresado)
        
        if user is not None:
            login(request, user)
            return redirect('homePage')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            
    return render(request, 'inicio/login.html')

# 2. VISTA DEL HOMEPAGE (Se mantiene)
@login_required
def homePage(request):
    return render(request, 'inicio/homePage.html')

# 3. CANDADO DE SEGURIDAD (Asegura que solo el admin general cree usuarios)
def es_admin_general(user):
    return user.is_superuser

# 4. VISTA PARA AGREGAR USUARIO (Totalmente refactorizada)
@login_required
@user_passes_test(es_admin_general, login_url='homePage')
def agregar_usuario_view(request):
    if request.method == 'POST':
        # Le entregamos todos los datos que llegaron del HTML a nuestro formulario
        form = RegistroUsuarioForm(request.POST)
        
        if form.is_valid():
            # form.save() hace la magia: crea el usuario, encripta la clave y guarda los checkboxes
            form.save() 
            messages.success(request, "¡Usuario y permisos guardados exitosamente!")
            return redirect('agregar_usuario') # Recargamos la página limpia
        else:
            # Si el formulario detecta un error (ej. el nombre de usuario ya existe), avisa
            messages.error(request, "Error al crear el usuario. Verifica los datos ingresados.")
    else:
        # Si la petición es GET (solo entrar a la pantalla), mandamos el formulario vacío a Yesenia
        form = RegistroUsuarioForm()

    return render(request, 'inicio/agregar_usuario.html', {'form': form})

# 5. VISTA DE LOGOUT (Se mantiene)
def logout_view(request):
    logout(request)
    return redirect('login')
