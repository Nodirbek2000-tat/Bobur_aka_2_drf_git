from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('magic/<str:token>/', views.magic_login, name='magic_login'),

    # API
    path('api/bot-auth/', views.bot_auth, name='bot_auth'),
    path('api/check-telegram/', views.check_telegram, name='check_telegram'),
    path('api/phone-lookup/', views.phone_lookup, name='phone_lookup'),
    path('api/me/', views.me, name='me'),

    # Foydalanuvchilar
    path('users/', views.users_list, name='users_list'),
    path('users/add/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    # Tumanlar
    path('districts/', views.districts_list, name='districts_list'),
    path('districts/add/', views.district_create, name='district_create'),
    path('districts/<int:pk>/delete/', views.district_delete, name='district_delete'),

    # MFYlar
    path('organizations/', views.organizations_list, name='organizations_list'),
    path('organizations/add/', views.organization_create, name='organization_create'),
    path('organizations/<int:pk>/delete/', views.organization_delete, name='organization_delete'),
]
