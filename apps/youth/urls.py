from django.urls import path
from . import views

app_name = 'youth'

urlpatterns = [
    path('', views.youth_list, name='list'),
    path('<int:pk>/', views.youth_detail, name='detail'),
    path('import/', views.import_excel, name='import'),
    path('import/sample/', views.sample_excel, name='sample_excel'),
    path('<int:pk>/sorovnoma/', views.youth_survey_view, name='survey'),
    path('api/list/', views.YouthListAPI.as_view(), name='api_list'),
    path('api/<int:pk>/', views.YouthDetailAPI.as_view(), name='api_detail'),
]
