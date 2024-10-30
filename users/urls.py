from django.urls import path
from .views import home, verification, profile, login_view

urlpatterns = [
    path('', home, name='home'),
    path('verification/', verification, name='verification'),
    path('profile/<str:phone>/', profile, name='profile'),
    path('login/', login_view, name='login'),  # Добавьте эту строку
]
