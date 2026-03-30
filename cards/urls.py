from django.urls import path

from . import views

app_name = 'cards'

urlpatterns = [
    # Player-facing
    path('', views.CollectionView.as_view(), name='collection'),
    path('<str:rarity>/', views.RarityDetailView.as_view(), name='rarity_detail'),

    # Staff card management
    path('manage/', views.CardManageListView.as_view(), name='manage_list'),
    path('manage/add/', views.CardCreateView.as_view(), name='manage_add'),
    path('manage/<uuid:card_id>/edit/', views.CardUpdateView.as_view(), name='manage_edit'),
    path('manage/<uuid:card_id>/delete/', views.CardDeleteView.as_view(), name='manage_delete'),
]
