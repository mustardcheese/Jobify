from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
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
    
    # Universal dashboard (redirects based on user type)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Messaging inbox and sent messages
    path('messages/inbox/', views.inbox, name='inbox'),
    path('messages/sent/', views.sent_messages, name='sent_messages'),
    
    # Individual message handling
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/reply/', views.reply_message, name='reply_message'),
    
    # Sending messages
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/send/<int:application_id>/', views.send_message, name='send_message_to_candidate'),
    
    # Application viewing for recruiters
    path('recruiter/application/<int:application_id>/', views.view_application, name='view_application'),
    path('messages/select-candidate/', views.select_candidate, name='select_candidate'),
    path('recruiter/application/<int:application_id>/', views.view_application, name='view_application'),
]