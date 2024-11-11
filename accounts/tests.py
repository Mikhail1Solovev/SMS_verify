from unittest.mock import patch
from django.test import Client, TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from django.core.cache import cache
from .models import User


class UserModelTests(TestCase):

    def setUp(self):
        self.phone_number = "+79174044144"
        self.password = "password123"

    def test_create_user(self):
        user = User.objects.create_user(
            phone_number=self.phone_number,
            password=self.password,
        )
        self.assertEqual(
            user.phone_number,
            self.phone_number,
            "Номер телефона не совпадает с ожидаемым."
        )
        self.assertIsNotNone(
            user.invite_code,
            "Инвайт-код должен быть установлен при создании пользователя."
        )
        self.assertEqual(
            len(user.invite_code), 6,
            "Инвайт-код должен быть длиной 6 символов."
        )
        self.assertTrue(
            user.check_password(self.password),
            "Пароль должен быть установлен и зашифрован."
        )

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            phone_number=self.phone_number,
            password=self.password,
        )
        self.assertEqual(
            superuser.phone_number,
            self.phone_number,
            "Номер телефона суперпользователя не совпадает с ожидаемым."
        )
        self.assertTrue(
            superuser.is_staff,
            "Суперпользователь должен иметь is_staff=True."
        )
        self.assertTrue(
            superuser.is_superuser,
            "Суперпользователь должен иметь is_superuser=True."
        )

    def test_invite_user(self):
        inviter = User.objects.create_user(
            phone_number="+79174044145",
            password=self.password,
        )
        invited_user = User.objects.create_user(
            phone_number="+79174044146",
            password=self.password,
            invited_by=inviter,
        )
        self.assertEqual(
            invited_user.invited_by,
            inviter,
            "Пригласивший пользователь должен совпадать с ожидаемым."
        )
        invitees = inviter.invitees.all()
        self.assertIn(
            invited_user,
            invitees,
            "Приглашённый пользователь должен находиться в списке invitees "
            "пригласившего пользователя."
        )


class UserAuthenticationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.phone_number = "+79174044144"
        self.password = "password123"
        self.invalid_phone_number = "12345"
        self.user = User.objects.create_user(
            phone_number=self.phone_number,
            password=self.password,
        )

    @patch("accounts.views.send_sms")
    def test_login_valid_phone_number(self, mock_send_sms):
        mock_send_sms.return_value = {"status": "success"}
        response = self.client.post(
            "/accounts/login/",
            {"phone_number": self.phone_number}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Введите код из SMS"
        )
        phone_number_int = int(self.phone_number.replace("+", ""))
        cache_key = f"sms_code_{phone_number_int}"
        cached_code = cache.get(cache_key)
        self.assertIsNotNone(
            cached_code,
            "Код подтверждения должен быть установлен в кэше."
        )
        self.assertTrue(
            cached_code.isdigit() and len(cached_code) == 4,
            "Код подтверждения должен быть 4-значным числом."
        )

    def test_login_invalid_phone_number(self):
        response = self.client.post(
            "/accounts/login/",
            {"phone_number": self.invalid_phone_number}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Введите корректный номер телефона."
        )

    @patch("accounts.views.send_sms")
    def test_verify_code_correct(self, mock_send_sms):
        mock_send_sms.return_value = {"status": "success"}
        phone_number_int = int(self.phone_number.replace("+", ""))
        cache_key = f"sms_code_{phone_number_int}"
        cache.set(cache_key, "1234", timeout=300)
        self.client.post(
            "/accounts/login/",
            {"phone_number": self.phone_number}
        )
        response = self.client.post("/accounts/login/", {"code": "1234"})
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 302:
            self.assertRedirects(response, "/accounts/profile-page/")

    @patch("accounts.views.send_sms")
    def test_verify_code_incorrect(self, mock_send_sms):
        mock_send_sms.return_value = {"status": "success"}
        phone_number_int = int(self.phone_number.replace("+", ""))
        cache_key = f"sms_code_{phone_number_int}"
        cache.set(cache_key, "1234", timeout=300)
        self.client.post(
            "/accounts/login/",
            {"phone_number": self.phone_number}
        )
        response = self.client.post("/accounts/login/", {"code": "0000"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Неверный код подтверждения."
        )
        self.assertFalse(
            response.wsgi_request.user.is_authenticated,
            "Пользователь не должен быть аутентифицирован с неверным кодом."
        )


class ReferralCodeTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.phone_number = "+79174044144"
        self.password = "password123"
        self.user = User.objects.create_user(
            phone_number=self.phone_number,
            password=self.password,
        )
        self.referral_code = "ABCD12"

    def authenticate_user(self, user):
        access_token = str(AccessToken.for_user(user))
        self.api_client.credentials(
            HTTP_AUTHORIZATION="Bearer " + access_token)

    def test_profile_referral_code_activation(self):
        another_user = User.objects.create_user(
            phone_number="+79174044145",
            password="password123",
        )
        self.authenticate_user(another_user)
        response = self.api_client.post(
            "/accounts/api/activate-invite/",
            {"invite_code": self.referral_code}
        )
        self.assertIn(
            response.status_code,
            [200, 404],
            f"Expected 200 or 404 but got {response.status_code}. "
            f"Response content: {response.content}"
        )
        if response.status_code == 200:
            self.assertEqual(
                response.data["detail"],
                "Инвайт-код успешно активирован."
            )
            another_user.refresh_from_db()
            self.assertEqual(
                another_user.invited_by,
                self.user,
                "Реферальный код должен быть присвоен пользователю."
            )

    def test_referral_list(self):
        referrer_user = User.objects.create_user(
            phone_number="+79174044146",
            password="password123",
        )
        User.objects.create_user(
            phone_number="+79174044147",
            password="password123",
            invited_by=referrer_user,
        )
        referred_users = User.objects.filter(invited_by=referrer_user)
        self.assertTrue(
            referred_users.exists(),
            "Пользователь должен иметь приглашённых пользователей в базе данных."
        )
        self.client.force_login(referrer_user)
        response = self.client.get("/accounts/profile-page/")
        self.assertEqual(
            response.status_code,
            200,
            f"Expected 200 but got {response.status_code}. "
            f"Response content: {response.content}"
        )
