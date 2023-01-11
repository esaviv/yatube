from django.utils import timezone


def year(request):
    """Добавляет в контекст переменную year - текущий год в виде числа."""
    return {
        'year': timezone.now().year,
    }
