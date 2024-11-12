from django.contrib.auth.views import LogoutView
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ActivateInviteCodeAPIView,
    LoginView,
    SendSMSView,
    UserProfileAPIView,
    index,
    profile,
)

urlpatterns = [
    path("", index, name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile-page/", profile, name="profile_page"),
    path("logout/", LogoutView.as_view(), name="logout"),  # Оставлен только один путь для logout
    path("api/profile/", UserProfileAPIView.as_view(), name="api_profile"),
    path(
        "api/activate-invite/",
        ActivateInviteCodeAPIView.as_view(),
        name="api_activate_invite",
    ),
    path("api/token/", TokenObtainPairView.as_view(),
         name="token_obtain_pair"),
    path("api/token/refresh/",
         TokenRefreshView.as_view(),
         name="token_refresh"),
    path("send-sms/", SendSMSView.as_view(), name="send_sms"),
]
