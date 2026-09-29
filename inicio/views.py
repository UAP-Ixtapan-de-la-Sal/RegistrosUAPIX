from django.shortcuts import render
from django.http import HttpResponse

def inicio(request):
    return HttpResponse("¡Bienvenido Chilly Willy!")

# Create your views here.
