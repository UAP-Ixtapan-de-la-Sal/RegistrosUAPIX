from datetime import datetime
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import connection, transaction
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET

from .models import Persona, RegistroActividadSala, UsuarioSistema
from .forms import RegistroClaseForm, RegistroEventoForm, RegistroUsuarioForm

# 1. VISTA DE LOGIN
def login_view(request):
    if request.method == 'POST':
        username_ingresado = request.POST.get('usuario')
        password_ingresado = request.POST.get('contrasena')
        
        user = authenticate(request, username=username_ingresado, password=password_ingresado)
        
        if user is not None:
            login(request, user)
            
            # Inicializamos el sello de tiempo estricto para el administrador
            request.session['ultima_actividad'] = datetime.now().timestamp()
            request.session.pop('admin_reautenticado', None)
            request.session.modified = True
            
            return redirect('homePage')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            
    return render(request, 'inicio/login.html')

# 2. VISTA DEL HOMEPAGE (Con control de inactividad de 1 min solo para superusuario)
@login_required
def homePage(request):
    if request.user.is_superuser:
        ahora = datetime.now().timestamp()
        
        # Si no existe un registro previo, lo inicializamos
        if 'ultima_actividad' not in request.session:
            request.session['ultima_actividad'] = ahora
            request.session.modified = True
            
        ultima_actividad = request.session.get('ultima_actividad')
        
        # Evaluamos si han pasado más de 10 segundos (10 segundos)
        if (ahora - ultima_actividad) > 10:
            logout(request)
            messages.error(request, "Sesión de administrador cerrada por inactividad de seguridad.")
            return redirect('login')
            
        # Actualizamos la marca de tiempo solo si el usuario interactúa explícitamente
        request.session['ultima_actividad'] = ahora
        request.session.modified = True
        
    # Los operadores comunes trabajan todo el día sin restricciones
    return render(request, 'inicio/homePage.html')

# 3. CANDADO DE SEGURIDAD
def es_admin_general(user):
    return user.is_superuser


def puede_acceder_sala_computo(user):
    return user.is_superuser or user.mod_sala_computo


class CatalogoAcademicoNoDisponible(Exception):
    pass


def _normalizar_nombre_bd(nombre):
    return ''.join(caracter.lower() for caracter in nombre if caracter.isalnum())


def _tabla_catalogo(cursor, tabla_logica, columnas_requeridas):
    tablas = connection.introspection.table_names(cursor)
    tabla = next(
        (nombre for nombre in tablas if _normalizar_nombre_bd(nombre) == _normalizar_nombre_bd(tabla_logica)),
        None,
    )
    if tabla is None:
        raise CatalogoAcademicoNoDisponible(f'No está disponible la tabla {tabla_logica}.')

    columnas = {
        _normalizar_nombre_bd(columna.name): columna.name
        for columna in connection.introspection.get_table_description(cursor, tabla)
    }
    resultado = {}
    for nombre_logico in columnas_requeridas:
        columna = columnas.get(_normalizar_nombre_bd(nombre_logico))
        if columna is None:
            raise CatalogoAcademicoNoDisponible(
                f'La tabla {tabla_logica} no contiene la columna {nombre_logico}.'
            )
        resultado[nombre_logico] = columna
    return tabla, resultado


def _catalogos_del_docente(docente):
    if not docente.id_carrera:
        return {'carreras': [], 'materias': [], 'grupos': []}

    with connection.cursor() as cursor:
        carrera_tabla, carrera_columnas = _tabla_catalogo(
            cursor,
            'CARRERA',
            ('ID_Carrera', 'Nombre_Carrera'),
        )
        materia_tabla, materia_columnas = _tabla_catalogo(
            cursor,
            'MATERIA',
            ('ID_Materia', 'Nombre_materia', 'ID_Carrera'),
        )
        grupo_tabla, grupo_columnas = _tabla_catalogo(
            cursor,
            'GRUPO',
            ('ID_Grupo', 'Nombre_Grupo', 'Semestre', 'Turno', 'ID_Carrera'),
        )
        quote = connection.ops.quote_name

        cursor.execute(
            f'SELECT {quote(carrera_columnas["ID_Carrera"])}, '
            f'{quote(carrera_columnas["Nombre_Carrera"])} '
            f'FROM {quote(carrera_tabla)} '
            f'WHERE {quote(carrera_columnas["ID_Carrera"])} = %s',
            [docente.id_carrera],
        )
        carrera = cursor.fetchone()
        if carrera is None:
            return {'carreras': [], 'materias': [], 'grupos': []}

        cursor.execute(
            f'SELECT {quote(materia_columnas["ID_Materia"])}, '
            f'{quote(materia_columnas["Nombre_materia"])} '
            f'FROM {quote(materia_tabla)} '
            f'WHERE {quote(materia_columnas["ID_Carrera"])} = %s '
            f'ORDER BY {quote(materia_columnas["Nombre_materia"])}',
            [docente.id_carrera],
        )
        materias = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]

        cursor.execute(
            f'SELECT {quote(grupo_columnas["ID_Grupo"])}, '
            f'{quote(grupo_columnas["Nombre_Grupo"])}, '
            f'{quote(grupo_columnas["Semestre"])}, '
            f'{quote(grupo_columnas["Turno"])} '
            f'FROM {quote(grupo_tabla)} '
            f'WHERE {quote(grupo_columnas["ID_Carrera"])} = %s '
            f'ORDER BY {quote(grupo_columnas["Nombre_Grupo"])}',
            [docente.id_carrera],
        )
        grupos = [
            {
                'id': row[0],
                'nombre': ' · '.join(str(valor) for valor in row[1:] if valor),
            }
            for row in cursor.fetchall()
        ]

    return {
        'carreras': [{'id': carrera[0], 'nombre': carrera[1]}],
        'materias': materias,
        'grupos': grupos,
    }


def _guardar_clases_recurrentes(form):
    docente = form.cleaned_data['numero_cuenta_docente']
    materia_id = form.cleaned_data['materia']
    grupo_id = form.cleaned_data['grupo']
    fecha = form.cleaned_data['fecha']
    fecha_fin = form.cleaned_data['fecha_fin_repeticion']
    dias = {int(dia) for dia in form.cleaned_data['dias_repeticion']}
    ocurrencias = []
    while fecha <= fecha_fin:
        if fecha.weekday() in dias:
            ocurrencias.append(fecha)
        fecha += timedelta(days=1)

    with connection.cursor() as cursor:
        tabla, columnas = _tabla_catalogo(
            cursor,
            'CLASE',
            ('ID_Materia', 'ID_Grupo', 'ID_Persona', 'Fecha', 'Hora_Inicio', 'Hora_Fin'),
        )
        quote = connection.ops.quote_name
        campos = [columnas[nombre] for nombre in (
            'ID_Materia',
            'ID_Grupo',
            'ID_Persona',
            'Fecha',
            'Hora_Inicio',
            'Hora_Fin',
        )]
        placeholders = ', '.join(['%s'] * len(campos))
        sql = (
            f'INSERT INTO {quote(tabla)} '
            f'({", ".join(quote(campo) for campo in campos)}) '
            f'VALUES ({placeholders})'
        )
        with transaction.atomic():
            for fecha_clase in ocurrencias:
                cursor.execute(sql, [
                    materia_id,
                    grupo_id,
                    docente.pk,
                    fecha_clase.isoformat(),
                    form.cleaned_data['hora_inicio'].isoformat(timespec='minutes'),
                    form.cleaned_data['hora_fin'].isoformat(timespec='minutes'),
                ])
    return len(ocurrencias)


def _guardar_evento(form):
    with connection.cursor() as cursor:
        tabla, columnas = _tabla_catalogo(
            cursor,
            'EVENTO-TALLERES-CONFERENCIAS',
            (
                'Tipo_Evento',
                'Nombre_Evento',
                'ID_Persona',
                'Nombre_Ponente_Externo',
                'Fecha',
                'Hora_Inicio',
                'Hora_Fin',
                'Estado_Bloque',
                'ID_Clase',
            ),
        )
        quote = connection.ops.quote_name
        campos = [columnas[nombre] for nombre in (
            'Tipo_Evento',
            'Nombre_Evento',
            'ID_Persona',
            'Nombre_Ponente_Externo',
            'Fecha',
            'Hora_Inicio',
            'Hora_Fin',
            'Estado_Bloque',
            'ID_Clase',
        )]
        sql = (
            f'INSERT INTO {quote(tabla)} '
            f'({", ".join(quote(campo) for campo in campos)}) '
            f'VALUES ({", ".join(["%s"] * len(campos))})'
        )
        persona = form.cleaned_data.get('persona')
        with transaction.atomic():
            cursor.execute(sql, [
                form.cleaned_data['tipo_evento'],
                form.cleaned_data['nombre_evento'],
                persona.pk if persona else None,
                '' if persona else form.cleaned_data['nombre_ponente_externo'],
                form.cleaned_data['fecha'].isoformat(),
                form.cleaned_data['hora_inicio'].isoformat(timespec='minutes'),
                form.cleaned_data['hora_fin'].isoformat(timespec='minutes'),
                'Reservado',
                None,
            ])


# 4. VISTA PARA AGREGAR USUARIO
@login_required
@user_passes_test(es_admin_general, login_url='homePage')
def agregar_usuario_view(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        
        if form.is_valid():
            form.save() 
            messages.success(request, "¡Usuario y Permisos Guardados Exitosamente!")
            return redirect('agregar_usuario')
        else:
            messages.error(request, "Error al crear el usuario. Verifica los datos ingresados.")
    else:
        form = RegistroUsuarioForm()

    return render(request, 'inicio/agregar_usuario.html', {'form': form})

# 5. VISTA DE LOGOUT
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
@user_passes_test(puede_acceder_sala_computo, login_url='homePage')
def sala_computo_view(request):
    catalogos_clase = {'carreras': [], 'materias': [], 'grupos': []}
    clase_form = RegistroClaseForm(catalogos=catalogos_clase)
    evento_form = RegistroEventoForm()
    active_schedule_view = ''

    if request.method == 'POST':
        categoria = request.POST.get('categoria')
        if categoria not in {
            RegistroActividadSala.CATEGORIA_CLASE,
            RegistroActividadSala.CATEGORIA_EVENTO,
        }:
            messages.error(request, 'Selecciona si deseas registrar una clase o un evento.')
            return redirect('sala_computo')

        active_schedule_view = categoria
        if categoria == RegistroActividadSala.CATEGORIA_CLASE:
            docente = Persona.objects.filter(
                matricula=request.POST.get('numero_cuenta_docente', '').strip(),
                perfil='Doc',
            ).first()
            if docente:
                try:
                    catalogos_clase = _catalogos_del_docente(docente)
                except CatalogoAcademicoNoDisponible as error:
                    messages.error(request, str(error))
            form = RegistroClaseForm(request.POST, catalogos=catalogos_clase)
        else:
            form = RegistroEventoForm(request.POST)

        if form.is_valid():
            if categoria == RegistroActividadSala.CATEGORIA_CLASE:
                try:
                    cantidad = _guardar_clases_recurrentes(form)
                except CatalogoAcademicoNoDisponible as error:
                    messages.error(request, str(error))
                    clase_form = form
                else:
                    messages.success(
                        request,
                        f'Se agendaron {cantidad} clases semanales hasta '
                        f'{form.cleaned_data["fecha_fin_repeticion"]:%d/%m/%Y}.',
                    )
                    return redirect(f'{reverse("sala_computo")}?agendar={categoria}')
            else:
                try:
                    _guardar_evento(form)
                except CatalogoAcademicoNoDisponible as error:
                    messages.error(request, str(error))
                    evento_form = form
                else:
                    messages.success(request, 'El evento se guardó correctamente.')
                    return redirect(f'{reverse("sala_computo")}?agendar={categoria}')
        if not form.is_valid() and categoria == RegistroActividadSala.CATEGORIA_CLASE:
            clase_form = form
        elif not form.is_valid() or categoria == RegistroActividadSala.CATEGORIA_EVENTO:
            evento_form = form
    else:
        categoria = request.GET.get('agendar')
        if categoria in {
            RegistroActividadSala.CATEGORIA_CLASE,
            RegistroActividadSala.CATEGORIA_EVENTO,
        }:
            active_schedule_view = categoria

    return render(request, 'inicio/sala-computo.html', {
        'clase_form': clase_form,
        'evento_form': evento_form,
        'active_schedule_view': active_schedule_view,
    })


@login_required
@user_passes_test(puede_acceder_sala_computo, login_url='homePage')
@require_GET
def buscar_docente_sala_view(request):
    numero_cuenta = request.GET.get('cuenta', '').strip()
    if not numero_cuenta:
        return JsonResponse({'encontrado': False}, status=400)

    docente = Persona.objects.filter(matricula=numero_cuenta, perfil='Doc').first()
    if docente is None:
        return JsonResponse({'encontrado': False}, status=404)

    try:
        catalogos = _catalogos_del_docente(docente)
    except CatalogoAcademicoNoDisponible as error:
        return JsonResponse({'encontrado': False, 'error': str(error)}, status=503)

    if not catalogos['carreras']:
        return JsonResponse({
            'encontrado': False,
            'error': 'La carrera del docente no se encuentra en el catálogo.',
        }, status=404)

    return JsonResponse({
        'encontrado': True,
        'persona_id': docente.pk,
        'carrera_id': docente.id_carrera,
        'nombre': f'{docente.nombre} {docente.apellidos}'.strip(),
        'carrera': catalogos['carreras'][0]['nombre'],
    })


@login_required
@user_passes_test(puede_acceder_sala_computo, login_url='homePage')
@require_GET
def catalogos_clase_docente_view(request):
    numero_cuenta = request.GET.get('cuenta', '').strip()
    carrera_id = request.GET.get('carrera', '').strip()
    docente = Persona.objects.filter(matricula=numero_cuenta, perfil='Doc').first()
    if docente is None:
        return JsonResponse({'error': 'No se encontró al docente.'}, status=404)

    if not carrera_id or str(docente.id_carrera) != carrera_id:
        return JsonResponse({'error': 'La carrera no corresponde al docente.'}, status=400)

    try:
        return JsonResponse(_catalogos_del_docente(docente))
    except CatalogoAcademicoNoDisponible as error:
        return JsonResponse({'error': str(error)}, status=503)


@login_required
@user_passes_test(puede_acceder_sala_computo, login_url='homePage')
@require_GET
def buscar_ponente_sala_view(request):
    numero_cuenta = request.GET.get('cuenta', '').strip()
    persona = Persona.objects.filter(matricula=numero_cuenta, perfil='Doc').first()
    if persona is None:
        return JsonResponse({'encontrado': False}, status=404)
    return JsonResponse({
        'encontrado': True,
        'persona_id': persona.pk,
        'nombre': f'{persona.nombre} {persona.apellidos}'.strip(),
    })


#6. VISTA DE AUDITORÍA Y REPORTES
@login_required
@user_passes_test(es_admin_general, login_url='homePage')
def auditoria_reportes_view(request):
    # Lógica para la vista de auditoría y reportes
    return render(request, 'inicio/auditoria_reportes.html')

#7. VISTA DE RESPALDOS DE BASE DE DATOS
@login_required
def respaldos_bd_view(request):
    # Lógica para la vista de respaldos de base de datos
    return render(request, 'inicio/respaldos_bd.html')