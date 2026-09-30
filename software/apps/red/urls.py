from django.urls import path

from . import views

urlpatterns = [
    path('', views.red, name='red'),
    path('bomba/', views.bomba, name='bomba'),
    path('<str:codigo>/', views.detalle, name='detalle'),
]
