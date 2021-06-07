from channels.db import database_sync_to_async

from .exceptions import ClientError
from .models import Room


@database_sync_to_async
def get_room_or_error(room_id, user):
    """
    Поиск комнаты для пользователя
    """
    # Проверка зарегистрирован ли пользователь
    if not user.is_authenticated:
        raise ClientError("USER_HAS_TO_LOGIN")
    # Поиск комнаты по запросу
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        raise ClientError("ROOM_INVALID")
    return room
