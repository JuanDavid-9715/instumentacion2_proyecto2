from django.urls import path

from . import views

urlpatterns = [
    path('', views.panel, name='panel'),
    path('prueba/', views.prueba, name='prueba'),
]
