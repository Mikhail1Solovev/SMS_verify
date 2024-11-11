# accounts/urls.py

from django.contrib.auth.views import LogoutView  # Импорт LogoutView
from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import (ActivateInviteCodeAPIView, LoginView, SendSMSView,
                    UserProfileAPIView, VerifyCodeView, index, profile)

urlpatterns = [
    path('', index, name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-code/<str:phone_number>/', VerifyCodeView.as_view(), name='verify_code'),
    path('profile-page/', profile, name='profile_page'),

    # API Endpoints
    path('api/profile/', UserProfileAPIView.as_view(), name='api_profile'),
    path('api/activate-invite/', ActivateInviteCodeAPIView.as_view(), name='api_activate_invite'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Дополнительные маршруты
    path('send-sms/', SendSMSView.as_view(), name='send_sms'),

    # Добавляем маршрут для logout
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
]
