from django.urls import path

from . import views

app_name = 'gameplay'

urlpatterns = [
    path('deck/', views.DeckView.as_view(), name='deck'),
    path('play/', views.PlayView.as_view(), name='play'),
    path('result/<int:pk>/', views.ResultView.as_view(), name='result'),
]
