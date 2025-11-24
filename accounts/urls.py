from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="accounts.signup"),
    path("login/", views.login, name="accounts.login"),
    path("logout/", views.logout, name="accounts.logout"),
    path("profile/", views.profile, name="accounts.profile"),
    path("profile/save/", views.save_profile, name="accounts.save_profile"),
    path("my-applications/", views.user_applications, name="user_applications"),
    path('recruiter/email-setup/', views.setup_recruiter_email, name='setup_recruiter_email'),
    path("search-candidates/", views.search_candidates, name="search_candidates"),
    path("save-search/", views.save_candidate_search, name="save_candidate_search"),
    path("saved-searches/", views.saved_candidate_searches, name="saved_candidate_searches"),
    path("saved-searches/delete/<int:search_id>/", views.delete_candidate_search, name="delete_candidate_search"),
]
