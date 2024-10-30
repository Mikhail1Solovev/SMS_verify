from django.contrib import admin
from django.urls import path, include
from users.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),  # Убедитесь, что у вас есть этот путь
    path('', home, name='home'),  # Добавляем маршрут для корневого URL
]
