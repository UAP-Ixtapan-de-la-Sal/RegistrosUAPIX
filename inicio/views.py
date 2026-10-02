from django.shortcuts import render
#from django.http import HttpResponse

 config-server
def inicio(request):
    return HttpResponse("¡Hola, mundo!")

#def inicio(request):
    #return HttpResponse("¡Bienvenido Chilly Willy!")
 main

def inicio(request):
    # Reemplaza 'inicio/index.html' con el nombre de la plantilla que vayas a usar
    return render(request, 'inicio/index.html') 
