#Esto es una prueba
from django.db import models

class Trabajador(models.Model):
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class Vehiculo(models.Model):
    placa = models.CharField(max_length=20, unique=True)
    marca = models.CharField(max_length=50)
    año = models.IntegerField() 
    trabajador_asignado = models.ForeignKey(Trabajador, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.placa