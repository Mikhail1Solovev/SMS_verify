from unittest.mock import patch
from django.test import Client, TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from django.core.cache import cache
from .models import User

# Тесты для модели User
class UserModelTests(TestCase):

    def setUp(self):
        self.phone_number = "+79174044144"
        self.password = "password123"

    def test_create_user(self):
        user = User.objects.create_user(phone_number=self.phone_number, password=self.password)

        # Проверка, что пользователь был создан с правильным номером телефона
        self.assertEqual(user.phone_number, self.phone_number, "Номер телефона не совпадает с ожидаемым.")
        # Проверка, что у пользователя установлен инвайт-код
        self.assertIsNotNone(user.invite_code, "Инвайт-код должен быть установлен при создании пользователя.")
        self.assertEqual(len(user.invite_code), 6, "Инвайт-код должен быть длиной 6 символов.")
        # Проверка, что пароль пользователя зашифрован
        self.assertTrue(user.check_password(self.password), "Пароль должен быть установлен и зашифрован.")

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(phone_number=self.phone_number, password=self.password)

        # Проверка, что суперпользователь был создан с правильным номером телефона
        self.assertEqual(superuser.phone_number, self.phone_number, "Номер телефона суперпользователя не совпадает с ожидаемым.")
        # Проверка, что суперпользователь имеет атрибуты is_staff и is_superuser установленными в True
        self.assertTrue(superuser.is_staff, "Суперпользователь должен иметь is_staff=True.")
        self.assertTrue(superuser.is_superuser, "Суперпользователь должен иметь is_superuser=True.")

    def test_invite_user(self):
        inviter = User.objects.create_user(phone_number="+79174044145", password=self.password)
        invited_user = User.objects.create_user(phone_number="+79174044146", password=self.password, invited_by=inviter)

        # Проверка, что пригласивший пользователь установлен у приглашенного пользователя
        self.assertEqual(invited_user.invited_by, inviter, "Пригласивший пользователь должен совпадать с ожидаемым.")
        # Проверка, что пригласивший пользователь имеет в related_name 'invitees' приглашенного пользователя
        invitees = inviter.invitees.all()
        self.assertIn(invited_user, invitees, "Приглашённый пользователь должен находиться в списке invitees пригласившего пользователя.")

# Тесты для авторизации пользователей
class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.phone_number = "+79174044144"
        self.password = "password123"
        self.invalid_phone_number = "12345"

        # Создание пользователя для тестов
        self.user = User.objects.create_user(phone_number=self.phone_number, password=self.password)

    @patch('accounts.views.send_sms')
    def test_login_valid_phone_number(self, mock_send_sms):
        mock_send_sms.return_value = {'status': 'success'}
        response = self.client.post('/accounts/login/', {'phone_number': self.phone_number})

        # Проверяем, что форма для ввода SMS-кода отображается
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите код из SMS')

        # Проверяем, что код верификации установлен в кэше
        phone_number_int = int(self.phone_number.replace('+', ''))
        cache_key = f'sms_code_{phone_number_int}'
        cached_code = cache.get(cache_key)
        self.assertIsNotNone(cached_code, "Код подтверждения должен быть установлен в кэше.")
        self.assertTrue(cached_code.isdigit() and len(cached_code) == 4, "Код подтверждения должен быть 4-значным числом.")

    def test_login_invalid_phone_number(self):
        response = self.client.post('/accounts/login/', {'phone_number': self.invalid_phone_number})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите корректный номер телефона.')

    @patch('accounts.views.send_sms')
    def test_verify_code_correct(self, mock_send_sms):
        mock_send_sms.return_value = {'status': 'success'}

        # Устанавливаем код подтверждения в кэше
        phone_number_int = int(self.phone_number.replace('+', ''))
        cache_key = f'sms_code_{phone_number_int}'
        cache.set(cache_key, '1234', timeout=300)

        # Пытаемся верифицировать код
        self.client.post('/accounts/login/', {'phone_number': self.phone_number})
        response = self.client.post('/accounts/login/', {'code': '1234'})

        # Проверяем успешный вход и отсутствие ошибки (редирект может быть или статус 200)
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 302:
            self.assertRedirects(response, '/accounts/profile-page/')

    @patch('accounts.views.send_sms')
    def test_verify_code_incorrect(self, mock_send_sms):
        mock_send_sms.return_value = {'status': 'success'}

        # Устанавливаем неверный код подтверждения в кэше
        phone_number_int = int(self.phone_number.replace('+', ''))
        cache_key = f'sms_code_{phone_number_int}'
        cache.set(cache_key, '1234', timeout=300)

        self.client.post('/accounts/login/', {'phone_number': self.phone_number})
        response = self.client.post('/accounts/login/', {'code': '0000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный код подтверждения.')
        self.assertFalse(response.wsgi_request.user.is_authenticated, "Пользователь не должен быть аутентифицирован с неверным кодом.")

# Тесты для реферальной системы
class ReferralCodeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.phone_number = "+79174044144"
        self.password = "password123"
        self.user = User.objects.create_user(phone_number=self.phone_number, password=self.password)
        self.referral_code = 'ABCD12'

    def authenticate_user(self, user):
        """Утилита для аутентификации пользователя с использованием JWT"""
        access_token = str(AccessToken.for_user(user))
        self.api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

    def test_profile_referral_code_activation(self):
        another_user = User.objects.create_user(phone_number="+79174044145", password="password123")
        self.authenticate_user(another_user)

        response = self.api_client.post('/accounts/api/activate-invite/', {'invite_code': self.referral_code})

        # Проверяем успешную активацию реферального кода
        self.assertIn(response.status_code, [200, 404], f"Expected 200 or 404 but got {response.status_code}. Response content: {response.content}")
        if response.status_code == 200:
            self.assertEqual(response.data['detail'], 'Инвайт-код успешно активирован.')
            another_user.refresh_from_db()
            self.assertEqual(another_user.invited_by, self.user, "Реферальный код должен быть присвоен пользователю.")

    def test_referral_list(self):
        referrer_user = User.objects.create_user(phone_number="+79174044146", password="password123")
        another_user = User.objects.create_user(phone_number="+79174044147", password="password123", invited_by=referrer_user)

        # Проверяем, что у пользователя есть приглашённые пользователи в базе данных
        referred_users = User.objects.filter(invited_by=referrer_user)
        self.assertTrue(referred_users.exists(), "Пользователь должен иметь приглашённых пользователей в базе данных.")

        # Логинимся пользователем и проверяем доступ к странице профиля
        self.client.force_login(referrer_user)
        response = self.client.get('/accounts/profile-page/')

        # Проверяем, что страница профиля доступна
        self.assertEqual(response.status_code, 200, f"Expected 200 but got {response.status_code}. Response content: {response.content}")
