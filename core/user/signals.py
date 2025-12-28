# core/user/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import AuthLog

@receiver(post_save, sender=AuthLog)
def notify_failed_logins(sender, instance, created, **kwargs):
    """Notifica cuando hay muchos intentos fallidos."""
    if created and instance.event_type == 'login_failed':
        # Contar intentos fallidos recientes
        recent_failures = AuthLog.objects.filter(
            user=instance.user,
            event_type='login_failed',
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_failures >= 5:
            send_mail(
                'Alerta: Múltiples intentos de login fallidos',
                f'Se detectaron {recent_failures} intentos fallidos para {instance.user.email}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMINS[0][1]],
                fail_silently=True,
            )