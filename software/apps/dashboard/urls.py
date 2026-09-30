from django.urls import path

from . import views

urlpatterns = [
    path('', views.panel, name='panel'),
    path('panel/datos/', views.panel_datos, name='panel-datos'),
    path('prueba/', views.prueba, name='prueba'),
]
