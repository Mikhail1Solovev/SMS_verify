from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import User


class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.phone_number = "+79174044144"
        self.password = "password123"
        self.invalid_phone_number = "12345"

        # Создаем пользователя для тестов
        self.user = User.objects.create_user(phone_number=self.phone_number, password=self.password)

    @patch('accounts.views.send_sms')
    def test_login_valid_phone_number(self, mock_send_sms):
        mock_send_sms.return_value = {'status': 'success'}
        response = self.client.post(reverse('login'), {'phone_number': self.phone_number, 'password': self.password})

        # Форматируем номер телефона
        formatted_phone = self.phone_number

        # Проверяем перенаправление на страницу проверки кода
        self.assertRedirects(response, reverse('verify_code', kwargs={'phone_number': formatted_phone}))

        # Проверяем, что код был установлен в кэш
        cache_key = f'sms_code_{self.phone_number}'
        cached_code = cache.get(cache_key)
        self.assertIsNotNone(cached_code, "Код подтверждения не установлен в кэш.")
        self.assertTrue(cached_code.isdigit() and len(cached_code) == 4,
                        "Код подтверждения должен быть 4-значным числом.")

    def test_login_invalid_phone_number(self):
        response = self.client.post(
            reverse('login'), {'phone_number': self.invalid_phone_number, 'password': 'any_password'})
        self.assertContains(response, 'Неверный номер телефона или пароль.', status_code=200)

    @patch('accounts.views.send_sms')
    def test_verify_code_correct(self, mock_send_sms):
        mock_send_sms.return_value = {'status': 'success'}

        # Устанавливаем код подтверждения в кэш
        cache_key = f'sms_code_{self.phone_number}'
        cache.set(cache_key, '1234', timeout=300)

        response = self.client.post(
            reverse('verify_code', kwargs={'phone_number': self.phone_number}), {'code': '1234'})
        self.assertRedirects(response, reverse('profile_page'))

    @patch('accounts.views.send_sms')
    def test_verify_code_incorrect(self, mock_send_sms):
        mock_send_sms.return_value = {'status': 'success'}

        # Устанавливаем неверный код подтверждения в кэш
        cache_key = f'sms_code_{self.phone_number}'
        cache.set(cache_key, '1234', timeout=300)

        response = self.client.post(
            reverse('verify_code', kwargs={'phone_number': self.phone_number}), {'code': '0000'})
        self.assertContains(response, 'Неверный код подтверждения.', status_code=200)
        self.assertFalse(response.wsgi_request.user.is_authenticated,
                         "Пользователь не должен быть аутентифицирован при неверном коде подтверждения.")


class InviteCodeTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user1 = User.objects.create_user(phone_number="+79170000001", password='password123')
        self.user2 = User.objects.create_user(phone_number="+79170000002", password='password123')

        # Получаем JWT токены для user2
        response = self.api_client.post(reverse('token_obtain_pair'), {
            'phone_number': self.user2.phone_number, 'password': 'password123'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.access_token = response.data['access']
        self.api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

    def test_activate_valid_invite_code(self):
        self.user1.invite_code = 'ABC123'
        self.user1.save()

        response = self.api_client.post(reverse('api_activate_invite'), {'invite_code': 'ABC123'}, format='json')
        self.assertEqual(response.status_code, 200)

        self.user2.refresh_from_db()
        self.assertEqual(self.user2.invited_by, self.user1)

    def test_activate_invalid_invite_code(self):
        User.objects.filter(invite_code='INVALID').delete()

        response = self.api_client.post(reverse('api_activate_invite'), {'invite_code': 'INVALID'}, format='json')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Инвайт-код не найден.', response.json()['detail'])

    def test_activate_already_activated_invite_code(self):
        self.user1.invite_code = 'ABC123'
        self.user1.save()
        self.user2.invited_by = self.user1
        self.user2.save()

        response = self.api_client.post(reverse('api_activate_invite'), {'invite_code': 'ABC123'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Вы уже активировали инвайт-код.', response.json()['detail'])

    def test_activate_own_invite_code(self):
        self.user2.invite_code = 'XYZ789'
        self.user2.save()

        response = self.api_client.post(reverse('api_activate_invite'), {'invite_code': 'XYZ789'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Нельзя использовать свой собственный инвайт-код.', response.json()['detail'])
