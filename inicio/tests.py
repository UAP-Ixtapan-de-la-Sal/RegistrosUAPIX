from django.test import TestCase
from django.urls import reverse

from .models import Trabajador


class RegistroTrabajadorTests(TestCase):
	def test_muestra_formulario_de_registro(self):
		response = self.client.get(reverse('registrar_trabajador'))

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'inicio/registro_trabajador.html')

	def test_guarda_trabajador_con_datos_validos(self):
		response = self.client.post(
			reverse('registrar_trabajador'),
			{'nombre': 'Ana Pérez', 'cargo': 'Coordinadora'},
		)

		self.assertRedirects(response, reverse('registrar_trabajador'))
		self.assertTrue(
			Trabajador.objects.filter(nombre='Ana Pérez', cargo='Coordinadora').exists()
		)