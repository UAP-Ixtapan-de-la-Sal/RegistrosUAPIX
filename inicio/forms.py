from django import forms

from .models import Trabajador


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombre', 'cargo']
        labels = {
            'nombre': 'Nombre completo',
            'cargo': 'Cargo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'autocomplete': 'name',
                'placeholder': 'Nombre completo',
            }),
            'cargo': forms.TextInput(attrs={
                'placeholder': 'Cargo del trabajador',
            }),
        }