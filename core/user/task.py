from celery import shared_task
from .services import UserService


@shared_task
def cleanup_expired_blacklist():
    """
    Limpia tokens expirados de la blacklist
    Ejecutar cada hora
    """
    count = UserService.cleanup_expired_blacklist()
    print(f"Tokens expirados eliminados: {count}")
    return count