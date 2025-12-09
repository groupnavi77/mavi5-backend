from ninja import Query, Router
from typing import List
from taggit.models import Tag 
from django.db.models import Q
from core.tag.api.schemas import TagAutocompleteOut


router = Router()
# TAG SECTION
@router.get(
    "/autocomplete", 
    response=List[TagAutocompleteOut],
    # Usamos la autenticación None ya que esta es una API pública (como AllowAny en DRF)
    url_name='tag-autocomplete'
)
def tag_autocomplete(request, q: str = None):
    """
    Busca etiquetas (Tags) para el widget de autocompletado en el Admin.
    Reemplaza TagAutocompleteAPIView.
    """
    queryset = Tag.objects.all()
    
    # 🌟 Lógica de Búsqueda (Reemplaza DRF SearchFilter)
    if q:
        # Usamos icontains (case-insensitive contains) en el campo 'name'
        # Esto imita el search_fields = ['name'] de DRF
        queryset = queryset.filter(name__icontains=q)
        
    # Opcional: Limitar los resultados a 20, como buena práctica de API de búsqueda.
    queryset = queryset[:20] 
    
    # Django Ninja serializa automáticamente el QuerySet al List[TagAutocompleteOut]
    return queryset