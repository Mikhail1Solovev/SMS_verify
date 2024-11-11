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
        response = self.client.post(reverse('login'), {'phone_number': self.phone_number})

        # Проверяем, что отображается форма для ввода кода подтверждения
        self.assertContains(response, 'Введите код из SMS', status_code=200)

        # Форматируем номер телефона для соответствия ключу кэша
        phone_number_int = int(self.phone_number.replace('+', ''))
        cache_key = f'sms_code_{phone_number_int}'

        # Проверяем, что код был установлен в кэш
        cached_code = cache.get(cache_key)
        self.assertIsNotNone(cached_code, "Код подтверждения не установлен в кэш.")
        self.assertTrue(cached_code.isdigit() and len(cached_code) == 4, "Код подтверждения должен быть 4-значным числом.")

    def test_login_invalid_phone_number(self):
        response = self.client.post(reverse('login'), {'phone_number': self.invalid_phone_number})
        self.assertContains(response, 'Введите корректный номер телефона.', status_code=200)

    @patch('accounts.views.send_sms')
    def test_verify_code_correct(self, mock_send_sms):
        mock_send_sms.return_value = {'status': 'success'}

        # Устанавливаем код подтверждения в кэш
        phone_number_int = int(self.phone_number.replace('+', ''))
        cache_key = f'sms_code_{phone_number_int}'
        cache.set(cache_key, '1234', timeout=300)

        # Эмулируем вход с правильным кодом
        response = self.client.post(reverse('login'), {'phone_number': self.phone_number})
        response = self.client.post(reverse('login'), {'code': '1234'})

        # Проверка на успешный вход: Проверяем наличие профиля в ответе
        self.assertContains(response, 'Профиль Пользователя', status_code=200)

    @patch('accounts.views.send_sms')
    def test_verify_code_incorrect(self, mock_send_sms):
        mock_send_sms.return_value = {'status': 'success'}

        # Устанавливаем неверный код подтверждения в кэш
        phone_number_int = int(self.phone_number.replace('+', ''))
        cache_key = f'sms_code_{phone_number_int}'
        cache.set(cache_key, '1234', timeout=300)

        response = self.client.post(reverse('login'), {'phone_number': self.phone_number})
        response = self.client.post(reverse('login'), {'code': '0000'})
        self.assertContains(response, 'Неверный код подтверждения.', status_code=200)
        self.assertFalse(response.wsgi_request.user.is_authenticated, "Пользователь не должен быть аутентифицирован при неверном коде подтверждения.")
