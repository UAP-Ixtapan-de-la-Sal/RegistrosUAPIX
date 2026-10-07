from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import Usuario

# Inicio de la Vista de Inicio de Sesión
def login_view(request):
    return render(request, 'inicio/login.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import Usuario

def login_view(request):
    if request.method == 'POST':
        # 1. Capturar los datos del formulario (incluyendo recuerdame)
        nombre_usuario = request.POST.get('usuario')
        contrasena_ingresada = request.POST.get('contrasena')
        recuerdame = request.POST.get('recuerdame')  # Devuelve 'on' si está marcado, None si no

        try:
            user = Usuario.objects.get(usuario=nombre_usuario)
            
            if check_password(contrasena_ingresada, user.contrasena):
                # Guardar datos en la sesión
                request.session['usuario_id'] = user.id
                request.session['usuario'] = user.usuario

                # 2. Evaluar recuerdame SOLO después de definirlo y validar las credenciales
                if recuerdame:
                    request.session.set_expiry(2592000)  # Mantener sesión por 30 días
                else:
                    request.session.set_expiry(60)       # Expira tras 60 segundos de inactividad

                return redirect('homePage')
            else:
                messages.error(request, 'Contraseña incorrecta.')

        except Usuario.DoesNotExist:
            messages.error(request, 'El usuario no existe.')

    # Si la petición es GET (cargar la página inicialmente), renderiza la plantilla
    return render(request, 'inicio/login.html')

def homePage(request):
    # 5. Control de acceso: Verificar si existe la sesión activa
    if 'usuario_id' not in request.session:
        # Si la sesión expiró (pasó el 1 min) o no ha iniciado sesión, redirigir al login
        return redirect('login')

    return render(request, 'inicio/homePage.html')

# Vista para cerrar sesión manualmente
def logout_view(request):
    request.session.flush() # Borra toda la información de la sesión activa
    return redirect('login')

#Vista de prueba para verificar que el servidor funciona correctamente
#from django.http import HttpResponse

#def inicio(request):
    #return HttpResponse("<h1>¡Servidor funcionando correctamente!</h1>") 
