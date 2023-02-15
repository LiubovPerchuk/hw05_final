from datetime import datetime


current_datetime = datetime.now()


def year(request):
    """Добавляет переменную с текущим годом."""
    return {"year": current_datetime.year}
