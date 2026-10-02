from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import TrabajadorForm


def registrar_trabajador(request):
    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trabajador registrado correctamente.')
            return redirect('registrar_trabajador')
    else:
        form = TrabajadorForm()

    return render(request, 'inicio/registro_trabajador.html', {'form': form})
