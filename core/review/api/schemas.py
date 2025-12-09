from ninja import Schema
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Review (Output) ---
class ReviewOut(Schema):
    id: int
    rating: int
    author: str
    text: str
    approved: bool
    created_at: datetime
    
    # Campo para la función FORMAT() (requiere acceso a timesince en el resolutor)
    # Nota: Es más limpio manejar esto en la capa de servicios o en el frontend.
    # Pero si lo necesitas en el backend:
    time_since: str 

    @staticmethod
    def resolve_time_since(obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at)

# --- Review (Input) ---
class ReviewIn(Schema):
    rating: int
    author: str
    text: str