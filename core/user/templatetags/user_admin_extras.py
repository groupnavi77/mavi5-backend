# core/user/templatetags/user_admin_extras.py

"""
Template tags personalizados para el admin de usuarios.
Estos tags ayudan a hacer cálculos y formateos en los templates.
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def mul(value, arg):
    """Multiplica dos valores."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divide dos valores."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def percentage(value, total):
    """Calcula el porcentaje."""
    try:
        if total == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0


@register.filter
def badge_color(provider):
    """Retorna el color del badge según el provider."""
    colors = {
        'email': '#6c757d',
        'google': '#4285f4',
        'facebook': '#1877f2',
        'github': '#333333'
    }
    return colors.get(provider, '#6c757d')


@register.filter
def event_icon(event_type):
    """Retorna el icono según el tipo de evento."""
    icons = {
        'login': '🔓',
        'logout': '🔒',
        'login_failed': '⚠️',
        'register': '✨',
        'password_reset': '🔑',
        'password_change': '🔐',
        'email_verify': '✉️',
        '2fa_verify': '🔐',
        '2fa_failed': '⚠️',
    }
    return icons.get(event_type, '📝')


@register.filter
def status_badge(is_active):
    """Retorna HTML para badge de estado."""
    if is_active:
        return mark_safe('<span class="badge green">✓ Activo</span>')
    return mark_safe('<span class="badge red">✗ Inactivo</span>')


@register.simple_tag
def progress_bar(value, total, color='blue'):
    """Genera una barra de progreso HTML."""
    try:
        percentage = (float(value) / float(total)) * 100 if total > 0 else 0
    except (ValueError, TypeError):
        percentage = 0
    
    html = f'''
    <div class="progress-bar" style="width: 100%; height: 20px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
        <div class="progress-fill" style="width: {percentage}%; height: 100%; background: {color}; transition: width 0.3s;"></div>
    </div>
    <small>{percentage:.1f}%</small>
    '''
    return mark_safe(html)


@register.filter
def time_ago(timestamp):
    """Convierte timestamp a formato 'hace X tiempo'."""
    from django.utils import timezone
    from datetime import timedelta
    
    if not timestamp:
        return 'Nunca'
    
    now = timezone.now()
    delta = now - timestamp
    
    if delta < timedelta(minutes=1):
        return 'Justo ahora'
    elif delta < timedelta(hours=1):
        minutes = int(delta.seconds / 60)
        return f'Hace {minutes} minuto{"s" if minutes != 1 else ""}'
    elif delta < timedelta(days=1):
        hours = int(delta.seconds / 3600)
        return f'Hace {hours} hora{"s" if hours != 1 else ""}'
    elif delta < timedelta(days=7):
        return f'Hace {delta.days} día{"s" if delta.days != 1 else ""}'
    elif delta < timedelta(days=30):
        weeks = delta.days // 7
        return f'Hace {weeks} semana{"s" if weeks != 1 else ""}'
    elif delta < timedelta(days=365):
        months = delta.days // 30
        return f'Hace {months} mes{"es" if months != 1 else ""}'
    else:
        years = delta.days // 365
        return f'Hace {years} año{"s" if years != 1 else ""}'


@register.filter
def format_ip(ip_address):
    """Formatea una dirección IP para mostrar."""
    if not ip_address:
        return 'N/A'
    return mark_safe(f'<code style="background: #f5f5f5; padding: 2px 5px;">{ip_address}</code>')


@register.filter
def json_pretty(value):
    """Formatea JSON de manera legible."""
    import json
    try:
        if isinstance(value, str):
            value = json.loads(value)
        return json.dumps(value, indent=2, ensure_ascii=False)
    except:
        return str(value)
