from .models import Notification


def notify_user(user, title, message, link=None, priority="INFO"):
    return Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        link=link,
        priority=priority
    )