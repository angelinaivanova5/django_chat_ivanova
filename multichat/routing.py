from django.urls import path

from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from chat.consumers import ChatConsumer


application = ProtocolTypeRouter({


    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("chat/stream/", ChatConsumer),
        ]),
    ),

})
