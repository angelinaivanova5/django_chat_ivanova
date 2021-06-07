from django.db import models


class Room(models.Model):
    """
    Комната
    """

    # Заголовок комнаты
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

    @property
    def group_name(self):
        """
        Возвращает имя комнаты, в которую сокет должен отправить сообщение если они есть
        """
        return "room-%s" % self.id
