from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/<uuid:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('settings/', views.UserSettingsView.as_view(), name='settings'),
]
