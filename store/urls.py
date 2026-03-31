from django.urls import path

from . import views

app_name = 'store'

urlpatterns = [
    path('', views.StoreView.as_view(), name='store'),
    path('open/<str:pack_type>/', views.PackOpenView.as_view(), name='open_pack'),
]
