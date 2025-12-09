from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.campaing.models import DiscountCampaign
from core.campaing.api.schemas import DiscountCampaignSchema

router = Router()

# 🎉 ENDPOINT: Listar campañas activas
@router.get(
    "/active",
    response=List[DiscountCampaignSchema],
    summary="Campañas activas",
    description="Lista todas las campañas de descuento actualmente activas"
)
def list_active_campaigns(request):
    """
    Lista todas las campañas activas en este momento.
    Útil para mostrar banners de promociones en el frontend.
    
    Ejemplo de uso:
    - Mostrar banner "BLACK FRIDAY: 50% de descuento"
    - Mostrar contador regresivo hasta el fin de la campaña
    """
    now = timezone.now()
    campaigns = DiscountCampaign.objects.filter(
        is_active=True,
        start_date__lte=now,
        expiration_date__gte=now
    ).order_by('-priority', '-start_date')
    
    return list(campaigns)


# 🎯 ENDPOINT: Campaña principal (mayor prioridad)
@router.get(
    "/featured",
    response=DiscountCampaignSchema,
    summary="Campaña destacada",
    description="Obtiene la campaña con mayor prioridad actualmente activa"
)
def get_featured_campaign(request):
    """
    Obtiene la campaña con mayor prioridad que esté activa.
    Útil para mostrar en el banner principal del sitio.
    """
    now = timezone.now()
    campaign = DiscountCampaign.objects.filter(
        is_active=True,
        start_date__lte=now,
        expiration_date__gte=now
    ).order_by('-priority').first()
    
    if not campaign:
        return None
    
    return campaign


# 🔍 ENDPOINT: Detalle de campaña por código
@router.get(
    "/{code}",
    response=DiscountCampaignSchema,
    summary="Detalle de campaña",
    description="Obtiene los detalles de una campaña por su código"
)
def get_campaign_by_code(request, code: str):
    """
    Obtiene una campaña específica por su código.
    
    Ejemplo:
    GET /api/campaigns/black-friday-2024
    """
    campaign = get_object_or_404(
        DiscountCampaign,
        code=code,
        is_active=True
    )
    return campaign


# 📅 ENDPOINT: Próximas campañas
@router.get(
    "/upcoming",
    response=List[DiscountCampaignSchema],
    summary="Próximas campañas",
    description="Lista campañas que empezarán próximamente"
)
def list_upcoming_campaigns(request):
    """
    Lista campañas que aún no han comenzado pero están programadas.
    Útil para mostrar "Próximamente: Cyber Monday".
    """
    now = timezone.now()
    campaigns = DiscountCampaign.objects.filter(
        is_active=True,
        start_date__gt=now
    ).order_by('start_date')[:5]  # Próximas 5 campañas
    
    return list(campaigns)