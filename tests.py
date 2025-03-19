from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser, ActivityLog
from django.contrib.auth import get_user_model
from accounts.models import Client, Driver, Vehicle, Transaction
from django.core.exceptions import ValidationError

from django.urls import reverse

class AuthTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='admin', password='testpass123', role='admin')
        self.user = CustomUser.objects.create_user(username='user', password='testpass123', role='user')

    def test_admin_access(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('client_list'))
        self.assertEqual(response.status_code, 200)

    def test_regular_user_restriction(self):
        self.client.login(username='user', password='testpass123')
        response = self.client.get(reverse('client_list'))
        self.assertEqual(response.status_code, 302)

class ActivityLogTests(TestCase):
    def test_activity_logging(self):
        user = CustomUser.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.client.get(reverse('client_list'))
        log = ActivityLog.objects.first()
        self.assertIsNotNone(log)
        self.assertIn('client_list', log.action)

class PermissionTests(TestCase):
    def test_edit_user_permission(self):
        admin = CustomUser.objects.create_user(username='admin', password='testpass123', role='admin')
        user = CustomUser.objects.create_user(username='user', password='testpass123', role='user')
        
        self.client.login(username='user', password='testpass123')
        response = self.client.get(reverse('edit_user', args=[admin.id]))
        self.assertEqual(response.status_code, 302)

        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('edit_user', args=[user.id]))
        self.assertEqual(response.status_code, 200)

class ClientCRUDTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='admin', password='testpass123', role='admin')
        self.client_obj = Client.objects.create(name='Test Client', phone_number='0123456789', address='Riyadh')

    def test_client_create_validation(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('client_create'), {
            'name': 'New Client',
            'phone_number': '0111222333',
            'address': 'Jeddah',
            'balance': 5000
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Client.objects.count(), 2)

class VehicleModelTests(TestCase):
    def test_vehicle_creation(self):
        driver = Driver.objects.create(name='Test Driver', phone_number='01012345678', license_number='AB1234')
        vehicle = Vehicle.objects.create(
            plate_number='ABC-123',
            oil_capacity=5000,
            driver=driver,
            purchase_date='2023-01-01',
            status='active'
        )
        self.assertEqual(vehicle.status, 'active')

class TransactionValidationTests(TestCase):
    def test_negative_amount_validation(self):
        client = Client.objects.create(name='Test Client')
        vehicle = Vehicle.objects.create(plate_number='TEST-123', oil_capacity=1000)
        
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                client=client,
                driver=Driver.objects.create(name='Test Driver', phone_number='01012345678', license_number='AB1234'),
                amount=-100,
                status='pending'
            ).full_clean()