from django.shortcuts import render
#from django.http import HttpResponse

#def inicio(request):
    #return HttpResponse("¡Bienvenido Chilly Willy!")

def inicio(request):
    # Reemplaza 'inicio/index.html' con el nombre de la plantilla que vayas a usar
    return render(request, 'inicio/index.html') 
