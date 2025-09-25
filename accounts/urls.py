from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="accounts.signup"),
    path("login/", views.login, name="accounts.login"),
    path("logout/", views.logout, name="accounts.logout"),
    path("profile/", views.profile, name="accounts.profile"),
    path("profile/save/", views.save_profile, name="accounts.save_profile"),
    path("my-applications/", views.user_applications, name="user_applications"),
]
