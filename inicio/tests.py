from django.test import TestCase
from django.urls import reverse
from django.db import connection

from .forms import RegistroClaseForm
from .models import Persona, RegistroActividadSala, UsuarioSistema


class SalaComputoViewTests(TestCase):
    def crear_tablas_academicas(self):
        with connection.cursor() as cursor:
            cursor.execute(
                'CREATE TABLE CARRERA (ID_Carrera INTEGER PRIMARY KEY, Nombre_Carrera VARCHAR(150))'
            )
            cursor.execute(
                'CREATE TABLE MATERIA (ID_Materia INTEGER PRIMARY KEY, Nombre_materia VARCHAR(150), ID_Carrera INTEGER)'
            )
            cursor.execute(
                'CREATE TABLE GRUPO (ID_Grupo INTEGER PRIMARY KEY, Nombre_Grupo VARCHAR(50), '
                'Semestre VARCHAR(30), Turno VARCHAR(30), ID_Carrera INTEGER)'
            )
            cursor.execute(
                'CREATE TABLE CLASE (ID_Clase INTEGER PRIMARY KEY AUTOINCREMENT, ID_Materia INTEGER, '
                'ID_Grupo INTEGER, ID_Persona INTEGER, Fecha DATE, Hora_Inicio TIME, Hora_Fin TIME)'
            )
            cursor.execute(
                'INSERT INTO CARRERA (ID_Carrera, Nombre_Carrera) VALUES (1, %s)',
                ['Ingeniería en Sistemas'],
            )
            cursor.execute(
                'INSERT INTO MATERIA (ID_Materia, Nombre_materia, ID_Carrera) VALUES (10, %s, 1)',
                ['Programación I'],
            )
            cursor.execute(
                'INSERT INTO GRUPO (ID_Grupo, Nombre_Grupo, Semestre, Turno, ID_Carrera) '
                'VALUES (20, %s, %s, %s, 1)',
                ['301', 'Tercero', 'Matutino'],
            )

    def crear_docente_con_catalogos(self, matricula='1234567890'):
        self.crear_tablas_academicas()
        docente = Persona.objects.create(
            matricula=matricula,
            perfil='Doc',
            nombre='Docente',
            apellidos='De Prueba',
            id_carrera=1,
        )
        return docente

    def test_superusuario_puede_abrir_panel(self):
        superusuario = UsuarioSistema.objects.create_superuser(
            username='administrador',
            password='Prueba-segura-123',
        )
        self.client.force_login(superusuario)

        response = self.client.get(reverse('sala_computo'))

        self.assertEqual(response.status_code, 200)

    def test_usuario_con_permiso_puede_abrir_panel(self):
        operador = UsuarioSistema.objects.create_user(
            username='operador_sala',
            password='Prueba-segura-123',
            mod_sala_computo=True,
        )
        self.client.force_login(operador)

        response = self.client.get(reverse('sala_computo'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sala de Cómputo')
        self.assertContains(response, 'Gestión de accesos y administración del espacio.')
        self.assertContains(response, 'Modo kiosco')
        self.assertContains(response, '¿Qué deseas agendar?')
        self.assertContains(response, "seleccionarTipoAgendamiento('clase')")
        self.assertContains(response, "seleccionarTipoAgendamiento('evento')")
        self.assertContains(response, 'Clase regular')
        self.assertEqual(
            [value for value, _ in RegistroClaseForm().fields['tipo_actividad'].choices],
            ['regular'],
        )
        self.assertContains(response, 'Agendar clase')
        self.assertContains(response, 'Agendar evento')
        self.assertContains(response, 'pertenece_al_plantel')
        self.assertContains(response, 'Estado de equipos')
        self.assertContains(response, 'Sesiones y clases activas del día')
        self.assertContains(response, '12')
        self.assertContains(response, '18')
        self.assertContains(response, 'Datos de ejemplo')
        self.assertNotContains(response, 'PORTAL DE GESTIÓN UAPIX')
        self.assertTemplateUsed(response, 'inicio/sala-computo.html')

    def test_operador_puede_registrar_una_clase(self):
        operador = UsuarioSistema.objects.create_user(
            username='operador_clase',
            password='Prueba-segura-123',
            mod_sala_computo=True,
        )
        docente = self.crear_docente_con_catalogos()
        self.client.force_login(operador)

        response = self.client.post(reverse('sala_computo'), {
            'categoria': 'clase',
            'tipo_actividad': 'regular',
            'numero_cuenta_docente': '1234567890',
            'docente_id': docente.pk,
            'carrera': 1,
            'materia': 10,
            'grupo': 20,
            'fecha': '2026-11-10',
            'fecha_fin_repeticion': '2026-11-20',
            'dias_repeticion': ['1'],
            'hora_inicio': '09:00',
            'hora_fin': '10:00',
        })

        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertContains(response, 'Se agendaron 2 clases semanales hasta 20/11/2026.')
        with connection.cursor() as cursor:
            cursor.execute('SELECT ID_Persona, ID_Materia, ID_Grupo, Fecha FROM CLASE ORDER BY Fecha')
            registros = cursor.fetchall()
        self.assertEqual(len(registros), 2)
        self.assertEqual([row[0:3] for row in registros], [(docente.pk, 10, 20)] * 2)
        self.assertEqual([str(row[3]) for row in registros], ['2026-11-10', '2026-11-17'])

    def test_operador_puede_registrar_un_evento(self):
        operador = UsuarioSistema.objects.create_user(
            username='operador_evento',
            password='Prueba-segura-123',
            mod_sala_computo=True,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                'CREATE TABLE "EVENTO-TALLERES-CONFERENCIAS" ('
                'ID_Evento INTEGER PRIMARY KEY, '
                'Tipo_Evento VARCHAR(50), '
                'Nombre_Evento VARCHAR(150), '
                'ID_Persona INTEGER, '
                'Nombre_Ponente_Externo VARCHAR(150), '
                'Fecha DATE, '
                'Hora_Inicio TIME, '
                'Hora_Fin TIME, '
                'Estado_Bloque VARCHAR(50), '
                'ID_Clase INTEGER)'
            )
        self.client.force_login(operador)

        response = self.client.post(reverse('sala_computo'), {
            'categoria': 'evento',
            'tipo_evento': 'Conferencia',
            'nombre_evento': 'Conferencia de prueba',
            'pertenece_al_plantel': 'no',
            'nombre_ponente_externo': 'Ponente de prueba',
            'fecha': '2026-11-11',
            'hora_inicio': '11:00',
            'hora_fin': '12:00',
        })

        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertContains(response, 'El evento se guardó correctamente.')
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT Tipo_Evento, Nombre_Evento, ID_Persona, '
                'Nombre_Ponente_Externo, Fecha, Hora_Inicio, Hora_Fin, '
                'Estado_Bloque, ID_Clase '
                'FROM "EVENTO-TALLERES-CONFERENCIAS"'
            )
            registro = cursor.fetchone()
        self.assertEqual(registro[0:4], ('Conferencia', 'Conferencia de prueba', None, 'Ponente de prueba'))
        self.assertEqual(str(registro[4]), '2026-11-11')
        self.assertEqual(str(registro[5]), '11:00:00')
        self.assertEqual(str(registro[6]), '12:00:00')
        self.assertEqual(registro[7:], ('Reservado', None))

    def test_no_registra_actividad_si_hora_fin_no_es_posterior(self):
        operador = UsuarioSistema.objects.create_user(
            username='operador_horario',
            password='Prueba-segura-123',
            mod_sala_computo=True,
        )
        docente = self.crear_docente_con_catalogos()
        self.client.force_login(operador)

        response = self.client.post(reverse('sala_computo'), {
            'categoria': 'clase',
            'tipo_actividad': 'regular',
            'numero_cuenta_docente': '1234567890',
            'docente_id': docente.pk,
            'carrera': 1,
            'materia': 10,
            'grupo': 20,
            'fecha': '2026-11-10',
            'fecha_fin_repeticion': '2026-11-20',
            'dias_repeticion': ['1'],
            'hora_inicio': '10:00',
            'hora_fin': '09:00',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'posterior a la hora de inicio')
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM CLASE')
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_no_registra_clase_con_numero_de_cuenta_que_no_es_docente(self):
        operador = UsuarioSistema.objects.create_user(
            username='operador_cuenta_invalida',
            password='Prueba-segura-123',
            mod_sala_computo=True,
        )
        self.client.force_login(operador)

        response = self.client.post(reverse('sala_computo'), {
            'categoria': 'clase',
            'tipo_actividad': 'regular',
            'numero_cuenta_docente': 'cuenta-inexistente',
            'docente_id': '',
            'carrera': '',
            'materia': '',
            'grupo': '',
            'fecha': '2026-11-10',
            'fecha_fin_repeticion': '2026-11-20',
            'dias_repeticion': ['1'],
            'hora_inicio': '09:00',
            'hora_fin': '10:00',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se encontró un docente con ese número de cuenta.')
        self.assertEqual(RegistroActividadSala.objects.count(), 0)

    def test_fecha_final_debe_ser_igual_o_posterior_a_fecha_inicial(self):
        operador = UsuarioSistema.objects.create_user(
            username='operador_periodo_invalido',
            password='Prueba-segura-123',
            mod_sala_computo=True,
        )
        docente = self.crear_docente_con_catalogos()
        self.client.force_login(operador)

        response = self.client.post(reverse('sala_computo'), {
            'categoria': 'clase',
            'tipo_actividad': 'regular',
            'numero_cuenta_docente': '1234567890',
            'docente_id': docente.pk,
            'carrera': 1,
            'materia': 10,
            'grupo': 20,
            'fecha': '2026-11-10',
            'fecha_fin_repeticion': '2026-11-09',
            'dias_repeticion': ['1'],
            'hora_inicio': '09:00',
            'hora_fin': '10:00',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'La fecha final debe ser igual o posterior a la fecha inicial.')
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM CLASE')
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_busqueda_por_cuenta_devuelve_nombre_del_docente(self):
        operador = UsuarioSistema.objects.create_user(
            username='operador_busqueda_docente',
            password='Prueba-segura-123',
            mod_sala_computo=True,
        )
        docente = self.crear_docente_con_catalogos('9876543210')
        docente.nombre = 'Ana'
        docente.apellidos = 'Docente'
        docente.save()
        self.client.force_login(operador)

        response = self.client.get(
            reverse('buscar_docente_sala'),
            {'cuenta': '9876543210'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'encontrado': True,
            'persona_id': docente.pk,
            'carrera_id': 1,
            'carrera': 'Ingeniería en Sistemas',
            'nombre': 'Ana Docente',
        })

    def test_catalogos_devuelve_materias_y_grupos_de_carrera_del_docente(self):
        operador = UsuarioSistema.objects.create_user(
            username='operador_catalogos',
            password='Prueba-segura-123',
            mod_sala_computo=True,
        )
        docente = self.crear_docente_con_catalogos()
        self.client.force_login(operador)

        response = self.client.get(
            reverse('catalogos_clase_docente'),
            {'cuenta': docente.matricula, 'carrera': 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'carreras': [{'id': 1, 'nombre': 'Ingeniería en Sistemas'}],
            'materias': [{'id': 10, 'nombre': 'Programación I'}],
            'grupos': [{'id': 20, 'nombre': '301 · Tercero · Matutino'}],
        })

    def test_usuario_sin_permiso_es_devuelto_al_portal(self):
        usuario = UsuarioSistema.objects.create_user(
            username='usuario_sin_modulo',
            password='Prueba-segura-123',
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse('sala_computo'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('homePage')))

    def test_usuario_no_autenticado_es_redirigido_al_login(self):
        response = self.client.get(reverse('sala_computo'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

# Create your tests here.
