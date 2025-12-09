from django.test import TestCase
from rest_framework.test import APIClient
from datetime import date

from ModuloBoletas.models import Boleta


class BoletasAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Crear boletas de prueba
        self.boleta1 = Boleta.objects.create(
            nombre='Juan Pérez González',
            rut='12345678-9',
            direccion='Calle Falsa 123',
            fecha_emision=date(2025, 11, 1),
            periodo_facturacion='2025-11',
            consumo=10.5,
            monto=15000.00,
        )
        self.boleta2 = Boleta.objects.create(
            nombre='María González López',
            rut='98765432-1',
            direccion='Av. Siempre Viva 742',
            fecha_emision=date(2025, 10, 1),
            periodo_facturacion='2025-10',
            consumo=8.25,
            monto=12000.00,
        )

    def test_consultar_by_rut_post(self):
        url = '/api/boletas/consultar/'
        resp = self.client.post(url, {'rut': '12345678-9'}, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # El endpoint puede devolver paginación -> normalizar
        if isinstance(data, dict) and 'results' in data:
            data_list = data['results']
        else:
            data_list = data
        # Debe devolver una lista con al menos una boleta
        self.assertIsInstance(data_list, list)
        self.assertTrue(any(b['rut'] == '12345678-9' for b in data_list))

    def test_por_rut_get(self):
        url = f'/api/boletas/por_rut/?rut=12345678-9'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        if isinstance(data, dict) and 'results' in data:
            data_list = data['results']
        else:
            data_list = data
        self.assertIsInstance(data_list, list)
        self.assertTrue(len(data_list) >= 1)

    def test_consultar_requires_criteria(self):
        url = '/api/boletas/consultar/'
        resp = self.client.post(url, {}, format='json')
        # Debe ser 400 por validación
        self.assertEqual(resp.status_code, 400)
