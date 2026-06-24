from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    # Web views
    path('', views.meetings_list, name='list'),
    path('statistika/', views.meetings_stats, name='stats'),
    path('<int:pk>/', views.meeting_detail, name='detail'),
    path('<int:pk>/pdf/', views.download_pdf, name='pdf'),
    path('verifications/', views.verifications_list, name='verifications'),
    path('logs/', views.action_logs, name='logs'),

    # Kamera
    path('camera/<str:session_id>/', views.camera_page, name='camera'),
    path('camera/<str:session_id>/upload/', views.camera_upload, name='camera_upload'),
    path('camera/<str:session_id>/status/', views.camera_status, name='camera_status'),

    # API endpoints (bot uchun)
    path('api/camera/create/', views.camera_create_api, name='api_camera_create'),
    path('api/list/', views.MeetingListCreateAPI.as_view(), name='api_list'),
    path('api/<int:pk>/', views.MeetingDetailAPI.as_view(), name='api_detail'),
    path('api/pending-verifications/', views.pending_verifications_api, name='api_pending'),
    path('api/<int:pk>/verify/', views.verify_meeting_api, name='api_verify'),
    path('api/<int:pk>/impossible/', views.impossible_meeting_api, name='api_impossible'),
    path('api/<int:pk>/force-approve/', views.admin_force_approve_api, name='api_force_approve'),
]
