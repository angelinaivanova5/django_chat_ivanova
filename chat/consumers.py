from django.conf import settings

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .exceptions import ClientError
from .models import Room


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    Работа с соединениями по websocket
    """

    async def connect(self):
        """
        Вызывается в начале первого соединения
        """
        # Проверка на то, залогинен ли пользователь или нет
        if self.scope["user"].is_anonymous:
            # Не пускаю
            await self.close()
        else:
            # Пускаю
            await self.accept()
        # Список комнат, в которые пользователь зашел в этом соединении
        self.rooms = set()

    async def receive_json(self, content):
        """
        Вызывается, когда из сокета приходит сообщение. Передает его дальше
        """
        # Тип события
        command = content.get("command", None)
        try:
            if command == "join":
                # Присоединение к комнате
                await self.join_room(content["room"])
            elif command == "leave":
                # Покидание комнаты
                await self.leave_room(content["room"])
            elif command == "send":
                await self.send_room(content["room"], content["message"])
        except ClientError as e:
            # Вернуть ошибки
            await self.send_json({"error": e.code})

    async def disconnect(self, code):
        """
        Вызывается, когда вебсокет отключается
        """
        # Покинуть все комнаты, в которых мы есть
        for room_id in list(self.rooms):
            try:
                await self.leave_room(room_id)
            except ClientError:
                pass

    # Методы ниже вызываются из receive_json

    async def join_room(self, room_id):
        """
        Присоединение к комнате
        """
        # Залогиненный пользователь в scope благодаря декоратору аутентификации
        room = Room.objects.get(pk=room_id)
        # Отправить в чат уведомление о новом участнике
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.join",
                "room_id": room_id,
                "username": self.scope["user"].username,
            }
        )
        # Запомнить что мы в этой комнате
        self.rooms.add(room_id)
        # Подписать пользователя на группу чтобы получать сообщения
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name,
        )
        # вернуть на клиент информацию по чату
        await self.send_json({
            "join": str(room.id),
            "title": room.title,
        })

    async def leave_room(self, room_id):
        """
        Вызывается когда пользовватель покидает комнату
        """
        room = Room.objects.get(pk=room_id)
        # Отправить уведомление о выходе пользоввателя в чат
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.leave",
                "room_id": room_id,
                "username": self.scope["user"].username,
            }
        )

        # Удалить себя из комнаты
        self.rooms.discard(room_id)
        # Отписать пользователя от комнаты (чтобы не приходили сообщения)
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name,
        )
        # Послать на клиент информацию о покидании комнаты
        await self.send_json({
            "leave": str(room.id),
        })

    async def send_room(self, room_id, message):
        """
        Вызывается когда кто-то посылает сообщение
        """
        # Проверить что они есть в этой комнате
        if room_id not in self.rooms:
            raise ClientError("ROOM_ACCESS_DENIED")
        # Отправить в соответствующую группу сообщение
        room = Room.objects.get(pk=room_id)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
                "room_id": room_id,
                "username": self.scope["user"].username,
                "message": message,
            }
        )

    # Вспомогательные методы для отправки разных типов сообщений

    async def chat_join(self, event):
        """
        Кто-то вошел в чат
        """
        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_ENTER,
                "room": event["room_id"],
                "username": event["username"],
            },
        )

    async def chat_leave(self, event):
        """
        Кто-то вышел из чата
        """
        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_LEAVE,
                "room": event["room_id"],
                "username": event["username"],
            },
        )

    async def chat_message(self, event):
        """
        Кто-то написал сообщение
        """
        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_MESSAGE,
                "room": event["room_id"],
                "username": event["username"],
                "message": event["message"],
            },
        )
