from ninja import Schema
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# ==============================================================================
# 1. ESQUEMAS ANIDADOS
# ==============================================================================

class DiscountCampaignSchema(Schema):
    """Schema para campañas de descuento"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    campaign_type: str
    discount: Decimal
    discount_type: str
    start_date: datetime
    expiration_date: datetime
    is_active: bool
    priority: int
