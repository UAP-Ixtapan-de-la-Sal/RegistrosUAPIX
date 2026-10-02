
from django.shortcuts import render, redirect
from .models import Trabajador

def registrar_trabajador(request):
    if request.method == 'POST':
        # 1. Recogemos los datos que vienen del formulario (POST)
        nombre_ingresado = request.POST.get('nombre')
        cargo_ingresado = request.POST.get('cargo')
        
        # 2. Guardamos el nuevo trabajador en la base de datos
        Trabajador.objects.create(
            nombre=nombre_ingresado,
            cargo=cargo_ingresado
        )
        
        # 3. Redirigimos a la misma vista (esto hace match con tu test 'assertRedirects')
        return redirect('registrar_trabajador')
    
    # Si la petición es GET, solo mostramos la plantilla HTML del formulario
    return render(request, 'inicio/registro_trabajador.html')
from django.shortcuts import render
#from django.http import HttpResponse

#def inicio(request):
    #return HttpResponse("¡Bienvenido Chilly Willy!")

def inicio(request):
    # Reemplaza 'inicio/index.html' con el nombre de la plantilla que vayas a usar
    return render(request, 'inicio/index.html') 

