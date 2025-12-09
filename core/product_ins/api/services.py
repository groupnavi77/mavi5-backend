from core.product_ins.models import Product
from django.db.models import QuerySet, Prefetch

class ProductService:
    """
    Servicio para manejar la lógica de negocio de productos.
    Usa métodos estáticos para funciones sin estado.
    """
    
    @staticmethod
    def get_optimized_queryset() -> QuerySet[Product]:
        """
        Devuelve el QuerySet base optimizado para evitar N+1 Queries.
        
        Optimizaciones aplicadas:
        - select_related: Para relaciones ForeignKey (Product_base, user)
        - prefetch_related: Para relaciones ManyToMany y reverse ForeignKey (tags, images)
        """
        queryset = Product.objects.select_related(
            'Product_base',  # Carga el ProductBase en una sola query
            'user'           # Carga el UserAccount en una sola query
        ).prefetch_related(
            'tag',                    # Carga los tags (ManyToMany)
            'product_images'          # Carga las imágenes relacionadas (reverse ForeignKey)
        )
        
        return queryset
    
    @staticmethod
    def list_products() -> QuerySet[Product]:
        """
        Lista los productos publicados, optimizado y ordenado.
        """
        return (
            ProductService.get_optimized_queryset()
            .filter(published=True)
            .order_by('-created_at')
        )
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Product:
        """
        Obtiene un producto por ID con todas las optimizaciones.
        """
        return ProductService.get_optimized_queryset().get(id=product_id)
    
    @staticmethod
    def get_product_by_key(key: str) -> Product:
        """
        Obtiene un producto por su key única.
        """
        return ProductService.get_optimized_queryset().get(key=key)