import logging
import random

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views import View
from django.http import HttpResponseNotAllowed
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from phonenumbers import (
    parse,
    is_valid_number,
    PhoneNumberFormat,
    format_number,
    NumberParseException,
)

from .utils import send_sms

User = get_user_model()
logger = logging.getLogger(__name__)


def index(request):
    return render(request, "accounts/index.html")


def profile(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "accounts/profile.html", {"user": request.user})


class LoginView(View):

    def get(self, request):
        # Сбрасываем состояние для нового запроса
        return render(request, "accounts/login.html", {"code_sent": False})

    def post(self, request):
        if "phone_number" in request.POST:
            # Обработка запроса на отправку SMS
            phone_number = request.POST.get("phone_number")
            try:
                # Проверка и форматирование номера телефона
                parsed_number = parse(phone_number, None)
                if not is_valid_number(parsed_number):
                    raise ValueError("Некорректный номер телефона")

                phone_number_int = int(
                    format_number(parsed_number, PhoneNumberFormat.E164)
                    .replace("+", "")
                )
                verification_code = str(random.randint(1000, 9999))
                cache_key = f"sms_code_{phone_number_int}"
                cache.set(cache_key, verification_code, timeout=300)

                send_sms(
                    phone=phone_number_int,
                    message=(
                        f"Ваш код подтверждения: {verification_code}"
                    ),
                )
                logger.debug(
                    f"Отправка SMS с кодом {verification_code} на номер "
                    f"{phone_number_int}"
                )

                request.session["phone_number"] = phone_number_int
                messages.success(
                    request, "Код подтверждения отправлен на ваш телефон."
                )
                return render(request, "accounts/login.html",
                              {"code_sent": True})

            except NumberParseException:
                messages.error(request, "Введите корректный номер телефона.")
                return render(request, "accounts/login.html",
                              {"code_sent": False})
            except Exception as e:
                logger.error(f"Непредвиденная ошибка: {e}")
                messages.error(
                    request,
                    "Произошла ошибка при отправке SMS. Пожалуйста, "
                    "попробуйте позже.",
                )
                return render(request, "accounts/login.html",
                              {"code_sent": False})

        elif "code" in request.POST:
            # Обработка кода подтверждения
            code = request.POST.get("code")
            phone_number = request.session.get("phone_number")
            cache_key = f"sms_code_{phone_number}"
            expected_code = cache.get(cache_key)

            # Логирование введенного и ожидаемого кода
            logger.debug(
                f"Введенный код: {code}, Ожидаемый код: {expected_code} "
                f"для номера: {phone_number}"
            )

            if expected_code == code:
                try:
                    user = User.objects.get(phone_number=phone_number)
                    login(request, user)
                    cache.delete(cache_key)
                    messages.success(request, "Вы успешно вошли.")
                    return redirect("profile_page")
                except User.DoesNotExist:
                    messages.error(request, "Пользователь не найден.")
                    return render(request, "accounts/login.html",
                                  {"code_sent": True})
            else:
                messages.error(request, "Неверный код подтверждения.")
                return render(request, "accounts/login.html",
                              {"code_sent": True})


class LogoutView(View):

    def post(self, request):
        logout(request)
        return redirect("login")

    def get(self, request):
        return HttpResponseNotAllowed(["POST"])


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "phone_number": user.phone_number,
            "invite_code": user.invite_code,
            "invited_by": (
                user.invited_by.phone_number if user.invited_by else None
            ),
        }
        return Response(data, status=status.HTTP_200_OK)


class ActivateInviteCodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        invite_code = request.data.get("invite_code")
        user = request.user

        if not invite_code:
            return Response(
                {"detail": "Инвайт-код не предоставлен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            inviter = User.objects.get(invite_code=invite_code)
        except User.DoesNotExist:
            return Response(
                {"detail": "Инвайт-код не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.invited_by:
            return Response(
                {"detail": "Вы уже активировали инвайт-код."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if inviter == user:
            return Response(
                {"detail": "Нельзя использовать свой собственный инвайт-код."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.invited_by = inviter
        user.save()

        return Response(
            {"detail": "Инвайт-код успешно активирован."},
            status=status.HTTP_200_OK
        )


class SendSMSView(View):

    def get(self, request):
        return render(request, "accounts/send_sms.html")

    def post(self, request):
        phone = request.POST.get("phone")
        message = request.POST.get("message")

        if not phone.startswith("+") or not phone[1:].isdigit():
            messages.error(request, "Неверный формат номера телефона.")
            return redirect("send_sms")

        response = send_sms(phone=phone, message=message)

        if response and response.get("status") == "success":
            messages.success(request, "SMS успешно отправлено!")
        else:
            error_message = response.get("error", "Неизвестная ошибка")
            messages.error(
                request,
                f"Ошибка при отправке SMS: {error_message}"
            )

        return redirect("send_sms")
