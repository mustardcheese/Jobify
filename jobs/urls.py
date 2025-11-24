from django.urls import path
from . import views

urlpatterns = [
    # =========================
    # Public / candidate-facing
    # =========================
    path("", views.job_list, name="job_list"),
    path("map/", views.job_map, name="job_map"),
    path("<int:job_id>/", views.job_detail, name="job_detail"),
    # Applying to jobs
    path("<int:job_id>/apply/", views.apply_to_job, name="apply_to_job"),
    path("<int:job_id>/quick-apply/", views.quick_apply, name="quick_apply"),
    path(
        "<int:job_id>/quick-apply/form/",
        views.quick_apply_form,
        name="quick_apply_form",
    ),
    # Candidate dashboards / activity
    path("my-applications/", views.my_applications, name="my_applications"),
    path("recommendations/", views.job_recommendations, name="job_recommendations"),
    path("user/dashboard/", views.user_dashboard, name="user_dashboard"),
    # =================================
    # Recruiter dashboard + job posting
    # =================================
    path("recruiter/dashboard/", views.recruiter_dashboard, name="recruiter_dashboard"),
    path("recruiter/create/", views.create_job, name="create_job"),
    # NEW: recruiter job edit
    path("recruiter/job/<int:job_id>/edit/", views.edit_job, name="edit_job"),
    # view applicants / map
    path(
        "recruiter/applicants/map/",
        views.recruiter_applicants_map,
        name="recruiter_applicants_map",
    ),
    path(
        "recruiter/application/<int:application_id>/",
        views.view_application,
        name="view_application",
    ),
    # small helper endpoint for location autocomplete
    path("api/geocode/", views.geocode_ajax, name="geocode_ajax"),
    # role-based redirect (decides recruiter vs candidate)
    path("dashboard/", views.dashboard, name="dashboard"),
    # =================
    # Messaging system
    # =================
    path("messages/inbox/", views.inbox, name="inbox"),
    path("messages/sent/", views.sent_messages, name="sent_messages"),
    # read / reply to a specific message
    path("messages/<int:message_id>/", views.message_detail, name="message_detail"),
    path("messages/<int:message_id>/reply/", views.reply_message, name="reply_message"),
    # send message (general or to a specific application/candidate)
    path("messages/send/", views.send_message, name="send_message"),
    path(
        "messages/send/<int:application_id>/",
        views.send_message,
        name="send_message_to_candidate",
    ),
    # recruiter picks which candidate to message
    path("messages/select-candidate/", views.select_candidate, name="select_candidate"),
    path("recruiter/jobs/", views.recruiter_job_list, name="recruiter_job_list"),
    # Candidate recommendations for recruiters
    path("recruiter/job/<int:job_id>/recommendations/", views.candidate_recommendations, name="candidate_recommendations"),
    #kanan-board
    path('job/<int:pk>/pipeline/', views.JobPipelineView.as_view(), name='job_pipeline'),
    path('applicant/<int:applicant_id>/move/', views.move_applicant, name='move_applicant'),
    path('applicant/<int:pk>/', views.ApplicantDetailView.as_view(), name='applicant_detail'),
]
