"""
ASGI config for heart_sync_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heart_sync_backend.settings")

# Django ASGI 애플리케이션 먼저 초기화 (반드시 import 전에!)
django_asgi_app = get_asgi_application()

# Django 초기화 후에 import
from channels.routing import ProtocolTypeRouter, URLRouter
from rooms.routing import websocket_urlpatterns

# HTTP와 WebSocket 라우팅 설정
application = ProtocolTypeRouter({
    "http" : django_asgi_app, # Http 요청 처리
    "websocket" : URLRouter(websocket_urlpatterns) # WebSockt 요청 처리
})
