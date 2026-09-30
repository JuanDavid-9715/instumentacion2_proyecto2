from django.urls import path

from . import views

urlpatterns = [
    path('', views.estadisticas, name='estadisticas'),
    path('datos/', views.datos, name='estadisticas-datos'),
]
