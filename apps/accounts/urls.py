from django.urls import path
from .views import signup, login_view, logout_view, csrf, me, mypage

urlpatterns = [
    path("csrf/", csrf, name="csrf"),
    path("signup/", signup, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("me/", me, name="me"),
    path("mypage/", mypage, name="mypage"),
]