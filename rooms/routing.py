from django.urls import path
from .consumers import GameConsumer

# WebSocket URL 패턴
websocket_urlpatterns = [
    path('ws/game/<str:room_id>/', GameConsumer.as_asgi()),
]