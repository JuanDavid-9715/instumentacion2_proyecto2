from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/flujos/', consumers.FlujoConsumer.as_asgi()),
]
