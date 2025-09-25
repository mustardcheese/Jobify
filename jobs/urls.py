from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('map/', views.job_map, name='job_map'),
    path('<int:job_id>/', views.job_detail, name='job_detail'),
    path('<int:job_id>/apply/', views.apply_to_job, name='apply_to_job'),
    path('<int:job_id>/quick-apply/', views.quick_apply, name='quick_apply'),
    path('<int:job_id>/quick-apply/form/', views.quick_apply_form, name='quick_apply_form'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('recommendations/', views.job_recommendations, name='job_recommendations'),
]
