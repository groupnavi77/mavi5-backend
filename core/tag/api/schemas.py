from ninja import Schema
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Tag  OUT ---
class TagAutocompleteOut(Schema):
    """Schema para devolver una etiqueta en el autocompletado."""
    id: int
    name: str

# Para la respuesta completa (lista de tags)
class TagListOut(Schema):
    items: List[TagAutocompleteOut]