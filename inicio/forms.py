from django import forms
from .models import UsuarioSistema

class RegistroUsuarioForm(forms.ModelForm):
    class Meta:
        model = UsuarioSistema
        # Incluimos los campos basándonos en tu diseño gráfico
        fields = [
            'username', 'password', 'rol', 
            'mod_sala_computo', 'mod_auto_acceso', 'mod_biblioteca', 
            'mod_prestamos', 'mod_insumos', 'mod_tecnologicos'
        ]
        widgets = {
            'password': forms.PasswordInput(), # Convierte el texto en asteriscos
        }

    def save(self, commit=True):
        # Pausamos el guardado automático
        user = super().save(commit=False)
        # Encriptamos la contraseña de forma segura
        user.set_password(self.cleaned_data["password"])
        # Reanudamos el guardado
        if commit:
            user.save()
        return user
