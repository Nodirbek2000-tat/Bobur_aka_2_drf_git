from django.urls import path
from . import views

urlpatterns = [
    path('', views.survey_list, name='survey_list'),
    path('<int:pk>/', views.survey_detail, name='survey_detail'),
    path('<int:pk>/delete/', views.survey_delete, name='survey_delete'),
    path('api/active/', views.api_active_survey, name='api_active_survey'),
]
