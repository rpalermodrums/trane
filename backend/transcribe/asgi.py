"""
ASGI config for transcribe project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

from core.consumers import ProcessingProgressConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transcribe.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path("ws/progress/<str:task_id>/", ProcessingProgressConsumer.as_asgi()),
            ])
        )
    ),
})
