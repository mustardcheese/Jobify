from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('map/', views.job_map, name='job_map'),
]