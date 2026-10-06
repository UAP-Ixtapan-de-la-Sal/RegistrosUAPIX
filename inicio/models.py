from django.db import models
from django.contrib.auth.hashers import make_password

class Usuario(models.Model):
    usuario = models.CharField(max_length=50, unique=True)
    contrasena = models.CharField(max_length=255)

    # Sobrescribimos el método save para encriptar la contraseña antes de guardarla en MariaDB
    def save(self, *args, **kwargs):
        # Evita volver a encriptar si la contraseña ya es un hash de Django
        if not self.contrasena.startswith('pbkdf2_sha256$'):
            self.contrasena = make_password(self.contrasena)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.usuario