from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Room


@login_required
def index(request):
    """
    Вид корневой страницы
    """
    # Получает список комнат в алфавитном порядке
    rooms = Room.objects.order_by("title")

    # Преобразует в template index.html
    return render(request, "index.html", {
        "rooms": rooms,
    })
