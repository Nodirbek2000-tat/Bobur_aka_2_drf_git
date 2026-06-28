from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    # Web views
    path('', views.meetings_list, name='list'),
    path('export/excel/', views.meetings_export_excel, name='export_excel'),
    path('statistika/', views.meetings_stats, name='stats'),
    path('<int:pk>/', views.meeting_detail, name='detail'),
    path('<int:pk>/pdf/', views.download_pdf, name='pdf'),
    path('<int:pk>/natija/', views.meeting_result_view, name='result'),
    path('<int:pk>/word/', views.download_word_doc, name='word'),
    path('verifications/', views.verifications_list, name='verifications'),
    path('logs/', views.action_logs, name='logs'),

    # Kamera
    path('camera/<str:session_id>/', views.camera_page, name='camera'),
    path('camera/<str:session_id>/upload/', views.camera_upload, name='camera_upload'),
    path('camera/<str:session_id>/status/', views.camera_status, name='camera_status'),

    # Bot/web statistika API
    path('api/my-youth/', views.bot_my_youth, name='api_my_youth'),
    path('api/youth/<int:pk>/stats/', views.bot_youth_detail, name='api_youth_stats'),
    path('api/my-yetakchilar/', views.bot_my_yetakchilar, name='api_my_yetakchilar'),
    path('api/my-stats/', views.bot_my_stats, name='api_my_stats'),

    # Telegram WebApp (yetakchi tasdiqlash)
    path('webapp/auth/', views.webapp_auth, name='webapp_auth'),
    path('webapp/uchrashuv/<int:pk>/', views.webapp_meeting, name='webapp_meeting'),
    path('webapp/uchrashuv/<int:pk>/tasdiqlash/', views.webapp_verify_action, name='webapp_verify'),

    # API endpoints (bot uchun)
    path('api/camera/create/', views.camera_create_api, name='api_camera_create'),
    path('api/list/', views.MeetingListCreateAPI.as_view(), name='api_list'),
    path('api/<int:pk>/', views.MeetingDetailAPI.as_view(), name='api_detail'),
    path('api/pending-verifications/', views.pending_verifications_api, name='api_pending'),
    path('api/<int:pk>/verify/', views.verify_meeting_api, name='api_verify'),
    path('api/<int:pk>/impossible/', views.impossible_meeting_api, name='api_impossible'),
    path('api/<int:pk>/force-approve/', views.admin_force_approve_api, name='api_force_approve'),
]
