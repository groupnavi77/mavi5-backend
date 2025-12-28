# core/category/api/schemas.py

from ninja import Schema, Field
from typing import Optional, List
from datetime import datetime

# ==============================================================================
# SCHEMAS DE LECTURA (Output)
# ==============================================================================

class CategorySchema(Schema):
    """Schema básico de categoría para listas."""
    id: int
    title: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: int
    cat_image_url: Optional[str] = None
    
    @staticmethod
    def resolve_cat_image_url(obj , context):
        """Resuelve la URL de la imagen."""
        # Si no hay imagen, salimos.
        if not obj.cat_image:
            return None
            
        image_url = obj.cat_image.url
        
        # 1. Chequeo de URL Absoluta (Producción S3)
        # Si la URL ya comienza con http/s, es S3. La devolvemos directamente.
        if image_url.startswith('http') or image_url.startswith('https'):
            return image_url
            
        # 2. Convertir Relativa a Absoluta (Desarrollo)
        # Si la URL es relativa y tenemos el objeto request (que debe estar
        # presente gracias a @paginate y la firma del endpoint).
        request = context.get('request')

        if request:
            # Esta es la magia que hace DRF: convierte /media/... a http://host:port/media/...
            return request.build_absolute_uri(image_url)
                
        # 3. Fallback: Devolver la URL relativa (Solo si falla el request, lo cual es raro)
        return image_url


class CategoryParentSchema(Schema):
    """Schema simplificado para categoría padre."""
    id: int
    title: str
    slug: str


class CategoryChildSchema(Schema):
    """Schema simplificado para hijos."""
    id: int
    title: str
    slug: str
    icon: Optional[str] = None


class CategorySiblingSchema(Schema):
    """Schema simplificado para hermanos."""
    id: int
    title: str
    slug: str


class CategoryDetailSchema(Schema):
    """Schema detallado de categoría con relaciones."""
    id: int
    title: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None
    cat_image_url: Optional[str] = None
    level: int
    parent_id: Optional[int] = None
    
    # Relaciones
    parent: Optional[CategoryParentSchema] = None
    children: List[CategoryChildSchema] = []
    siblings: List[CategorySiblingSchema] = []
    
    # Estadísticas
    children_count: int = 0
    descendants_count: int = 0
    # products_count: int = 0  # Descomentar si tienes productos


class CategoryTreeSchema(Schema):
    """Schema para árbol jerárquico de categorías."""
    id: int
    title: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None
    cat_image_url: Optional[str] = None
    level: int
    parent_id: Optional[int] = None
    children: List['CategoryTreeSchema'] = []


# Necesario para la referencia recursiva
CategoryTreeSchema.model_rebuild()


# ==============================================================================
# SCHEMAS DE ESCRITURA (Input)
# ==============================================================================

class CategoryCreateSchema(Schema):
    """Schema para crear una nueva categoría."""
    title: str = Field(..., min_length=1, max_length=50)
    slug: Optional[str] = Field(None, max_length=100)
    icon: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Electrónica",
                "slug": "electronica",
                "icon": "fa-laptop",
                "description": "Productos electrónicos y tecnología",
                "parent_id": None
            }
        }


class CategoryUpdateSchema(Schema):
    """Schema para actualizar una categoría."""
    title: Optional[str] = Field(None, min_length=1, max_length=50)
    slug: Optional[str] = Field(None, max_length=100)
    icon: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Electrónica y Tecnología",
                "description": "Productos electrónicos, tecnología y gadgets"
            }
        }


# ==============================================================================
# SCHEMAS DE FILTROS
# ==============================================================================

class CategoryFilterSchema(Schema):
    """Schema para filtrar categorías."""
    search: Optional[str] = Field(
        None, 
        description="Buscar en título, descripción o slug"
    )
    parent_id: Optional[int] = Field(
        None, 
        description="ID del padre (0 para categorías raíz)"
    )
    level: Optional[int] = Field(
        None, 
        ge=0,
        description="Nivel en el árbol (0=raíz, 1=primer nivel, etc)"
    )
    has_children: Optional[bool] = Field(
        None,
        description="true: solo con hijos, false: solo sin hijos"
    )
    root_only: bool = Field(
        False,
        description="Solo categorías raíz (nivel 0)"
    )
    ordering: Optional[str] = Field(
        None,
        description="Ordenamiento: 'title', '-title', 'level', 'tree'"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "search": "electr",
                "level": 0,
                "root_only": True,
                "ordering": "title"
            }
        }


# ==============================================================================
# SCHEMAS DE RESPUESTA
# ==============================================================================

class CategoryResponseSchema(Schema):
    """Schema de respuesta genérica."""
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None


class CategoryStatsSchema(Schema):
    """Schema para estadísticas de categorías."""
    total_categories: int
    root_categories: int
    leaf_categories: int
    levels: dict
    max_depth: int