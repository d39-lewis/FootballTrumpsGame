from django.urls import path

from . import views

app_name = 'cards'

urlpatterns = [
    path('', views.CollectionView.as_view(), name='collection'),
    path('<str:rarity>/', views.RarityDetailView.as_view(), name='rarity_detail'),
]
