# api/tests.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.hashers import make_password

from service.models import User, Company, Station


class TestStationApi(APITestCase):

    def setUp(self):
        # Create user
        self.user = User.objects.create(
            username='testuser',
            full_name='Test User',
            email='test@example.com',
            role='manager',              # ✅ use actual value
            password=make_password('testpassword'),
        )

        # Create company (owner required)
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user
        )

        # Attach company to user
        self.user.company = self.company
        self.user.save()

        # Create station
        self.station = Station.objects.create(
            name='Station One',
            company=self.company,
            location='Test Location'
        )

        # Router name: basename='station' → station-list
        self.url = reverse('station-list')

    def test_unauthenticated_access_is_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access_is_allowed(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_station_list_returns_data(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Station One')
class TestTransactionApi(APITestCase):

    def setUp(self):
        self.user = User.objects.create(
            username='cashier',
            full_name='Cashier',
            email='cashier@test.com',
            role='attendant',
            password=make_password('pass1234'),
        )

        self.company = Company.objects.create(
            name='Fuel Corp',
            owner=self.user
        )

        self.user.company = self.company
        self.user.save()

        self.station = Station.objects.create(
            name='Main Station',
            company=self.company,
            location='City'
        )

        self.url = '/api/v1/transactions/create/'

    def test_transaction_requires_authentication(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_transaction_success(self):
        self.client.login(username='cashier', password='pass1234')

        payload = {
            "station": self.station.id,
            "amount": 50,
            "fuel_type": "petrol"
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
