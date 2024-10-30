# users/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .sms import send_sms  # Импортируйте функцию отправки SMS
from .models import User
import random


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        # Генерация и сохранение кода верификации
        verification_code = str(random.randint(1000, 9999))

        # Сохранение пользователя в базе данных или обновление существующего
        user, created = User.objects.get_or_create(phone=phone)
        user.verification_code = verification_code
        user.save()

        # Отправка SMS с кодом верификации
        send_sms(phone, f"Your verification code is: {verification_code}")

        return redirect('verification')

    return render(request, 'login.html')


def verification(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        code = request.POST.get('code')

        try:
            user = User.objects.get(phone=phone)
            if user.verification_code == code:
                return redirect('profile', phone=phone)
            else:
                return HttpResponse("Verification code is incorrect.")
        except User.DoesNotExist:
            return HttpResponse("User not found.")

    return render(request, 'verification.html')


def profile(request, phone):
    try:
        user = User.objects.get(phone=phone)
        return render(request, 'profile.html', {'phone': user.phone, 'invite_code': user.invite_code})
    except User.DoesNotExist:
        return HttpResponse("User not found.")
