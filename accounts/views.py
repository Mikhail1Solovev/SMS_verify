# accounts/views.py

import logging
import random

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views import View
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .utils import send_sms

User = get_user_model()

# Настройка логирования
logger = logging.getLogger(__name__)


def index(request):
    """
    Главная страница приложения accounts.
    """
    return render(request, 'accounts/index.html')  # Убедитесь, что шаблон существует


def profile(request):
    """
    Страница профиля пользователя.
    """
    if not request.user.is_authenticated:
        return redirect('login')  # Перенаправление на страницу входа, если пользователь не аутентифицирован
    return render(request, 'accounts/profile.html', {'user': request.user})  # Убедитесь, что шаблон существует


class LoginView(View):
    """
    Представление для логина пользователя.
    """

    def get(self, request):
        return render(request, 'accounts/login.html')  # Убедитесь, что шаблон существует

    def post(self, request):
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')

        user = authenticate(request, phone_number=phone_number, password=password)
        if user is not None:
            # Генерация кода подтверждения
            verification_code = str(random.randint(1000, 9999))
            # Сохранение кода в кэш с ключом 'sms_code_{phone_number}'
            cache_key = f'sms_code_{phone_number}'
            cache.set(cache_key, verification_code, timeout=300)  # Код действителен 5 минут

            # Отправка кода через SMS
            response = send_sms(phone=phone_number, message=f"Ваш код подтверждения: {verification_code}")
            if response.get('status') == 'success':
                messages.success(request, 'Код подтверждения отправлен на ваш телефон.')
                # Перенаправление на страницу проверки кода
                return redirect('verify_code', phone_number=phone_number)
            else:
                messages.error(request, f"Ошибка при отправке SMS: {response.get('error', 'Неизвестная ошибка')}")
                return render(request, 'accounts/login.html')
        else:
            messages.error(request, 'Неверный номер телефона или пароль.')
            return render(request, 'accounts/login.html')


class VerifyCodeView(View):
    """
    Представление для проверки кода подтверждения.
    """

    def get(self, request, phone_number):
        return render(request, 'accounts/verify_code.html', {'phone_number': phone_number})

    def post(self, request, phone_number):
        code = request.POST.get('code')
        cache_key = f'sms_code_{phone_number}'
        expected_code = cache.get(cache_key)

        # Добавляем логирование для отладки
        logger.debug(f"VerifyCodeView: phone_number={phone_number}, code={code}, expected_code={expected_code}")

        if expected_code == code:
            try:
                user = User.objects.get(phone_number=phone_number)
                login(request, user)
                # Удаление кода из кэша после успешной проверки
                cache.delete(cache_key)
                logger.debug("User authenticated successfully.")
                return redirect('profile_page')
            except User.DoesNotExist:
                messages.error(request, 'Пользователь не найден.')
                logger.error("User does not exist.")
                return render(request, 'accounts/verify_code.html', {'phone_number': phone_number})
        else:
            messages.error(request, 'Неверный код подтверждения.')
            logger.warning("Incorrect verification code entered.")
            return render(request, 'accounts/verify_code.html', {'phone_number': phone_number})


class UserProfileAPIView(APIView):
    """
    API для получения профиля пользователя.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'phone_number': user.phone_number,
            'invite_code': user.invite_code,
            'invited_by': user.invited_by.phone_number if user.invited_by else None,
        }
        return Response(data, status=status.HTTP_200_OK)


class ActivateInviteCodeAPIView(APIView):
    """
    API для активации инвайт-кода.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        invite_code = request.data.get('invite_code')
        user = request.user  # Предполагается, что пользователь аутентифицирован

        if not invite_code:
            return Response(
                {"detail": "Инвайт-код не предоставлен."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            inviter = User.objects.get(invite_code=invite_code)
        except User.DoesNotExist:
            return Response(
                {"detail": "Инвайт-код не найден."},
                status=status.HTTP_404_NOT_FOUND  # Возвращаем 404
            )

        if user.invited_by:
            return Response(
                {"detail": "Вы уже активировали инвайт-код."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if inviter == user:
            return Response(
                {"detail": "Нельзя использовать свой собственный инвайт-код."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.invited_by = inviter
        user.save()

        return Response(
            {"detail": "Инвайт-код успешно активирован."},
            status=status.HTTP_200_OK
        )


class SendSMSView(View):
    """
    Представление для отправки SMS.
    """

    def get(self, request):
        return render(request, 'accounts/send_sms.html')  # Убедитесь, что шаблон существует

    def post(self, request):
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        # Проверяем формат номера телефона (например, начинается с '+')
        if not phone.startswith('+') or not phone[1:].isdigit():
            messages.error(request, 'Неверный формат номера телефона.')
            return redirect('send_sms')

        response = send_sms(phone=phone, message=message)

        if response and response.get('status') == 'success':
            messages.success(request, 'SMS успешно отправлено!')
        else:
            error_message = response.get('error', 'Неизвестная ошибка')
            messages.error(request, f"Ошибка при отправке SMS: {error_message}")

        return redirect('send_sms')
