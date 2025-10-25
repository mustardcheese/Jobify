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
    # User dashboard
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    # Recruiter views
    path('recruiter/dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('recruiter/create/', views.create_job, name='create_job'),
    path('api/geocode/', views.geocode_ajax, name='geocode_ajax'),
]
