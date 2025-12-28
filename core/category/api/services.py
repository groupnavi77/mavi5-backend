# core/category/api/services.py

"""
Servicios de lógica de negocio para Categorías.
Contiene toda la lógica de negocio, validaciones y operaciones complejas.
"""

from typing import List, Optional, Dict, Tuple
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from django.core.cache import cache
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from ..models import Category


class CategoryService:
    """Servicio principal para gestión de categorías."""
    
    # ===========================================================================
    # MÉTODOS DE CONSULTA Y BÚSQUEDA
    # ===========================================================================
    
    @staticmethod
    def get_all_categories(
        search: Optional[str] = None,
        parent_id: Optional[int] = None,
        level: Optional[int] = None,
        has_children: Optional[bool] = None,
        root_only: bool = False,
        ordering: str = 'tree'
    ):
        """
        Obtiene categorías con filtros aplicados.
        
        Args:
            search: Búsqueda en título, slug, descripción
            parent_id: Filtrar por padre (0 = raíz, None = todos)
            level: Nivel en el árbol
            has_children: Solo con/sin hijos
            root_only: Solo categorías raíz
            ordering: Tipo de ordenamiento
        
        Returns:
            QuerySet de categorías filtradas
        """
        queryset = Category.objects.all()
        
        # Búsqueda
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(slug__icontains=search)
            )
        
        # Filtro por padre
        if parent_id is not None:
            if parent_id == 0:
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)
        
        # Filtro por nivel
        if level is not None:
            queryset = queryset.filter(level=level)
        
        # Solo raíz
        if root_only:
            queryset = queryset.filter(level=0)
        
        # Filtro por hijos
        if has_children is not None:
            if has_children:
                queryset = queryset.filter(children__isnull=False).distinct()
            else:
                queryset = queryset.filter(children__isnull=True)
        
        # Ordenamiento
        queryset = CategoryService._apply_ordering(queryset, ordering)
        
        return queryset
    
    @staticmethod
    def _apply_ordering(queryset, ordering: str):
        """Aplica ordenamiento al queryset."""
        if ordering == 'title':
            return queryset.order_by('title')
        elif ordering == '-title':
            return queryset.order_by('-title')
        elif ordering == 'level':
            return queryset.order_by('level', 'title')
        elif ordering == 'tree':
            return queryset.order_by('tree_id', 'lft')
        else:
            return queryset.order_by('tree_id', 'lft')
    
    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Category]:
        """Obtiene una categoría por ID."""
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return None
    
    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[Category]:
        """Obtiene una categoría por slug."""
        try:
            return Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return None
    
    @staticmethod
    def search_categories(query: str, limit: int = 10) -> List[Category]:
        """
        Búsqueda rápida de categorías.
        
        Args:
            query: Término de búsqueda
            limit: Máximo de resultados
        
        Returns:
            Lista de categorías encontradas
        """
        if not query or len(query) < 2:
            return []
        
        categories = Category.objects.filter(
            Q(title__icontains=query) |
            Q(slug__icontains=query) |
            Q(description__icontains=query)
        ).order_by('level', 'title')[:limit]
        
        return list(categories)
    
    # ===========================================================================
    # MÉTODOS DE ÁRBOL Y JERARQUÍA
    # ===========================================================================
    
    @staticmethod
    def get_tree(parent_id: Optional[int] = None, use_cache: bool = True) -> List[Dict]:
        """
        Obtiene el árbol de categorías en formato jerárquico.
        
        Args:
            parent_id: ID del nodo raíz (None = todas las raíces)
            use_cache: Usar caché (recomendado)
        
        Returns:
            Lista de diccionarios con estructura de árbol
        """
        cache_key = f'category_tree_{parent_id}'
        
        # Intentar obtener del caché
        if use_cache:
            cached_tree = cache.get(cache_key)
            if cached_tree:
                return cached_tree
        
        # Construir árbol
        if parent_id:
            try:
                parent = Category.objects.get(id=parent_id)
                categories = parent.get_descendants(include_self=True)
            except Category.DoesNotExist:
                return []
        else:
            categories = Category.objects.filter(level=0)
        
        tree = [CategoryService._build_tree_node(cat) for cat in categories]
        
        # Guardar en caché por 1 hora
        if use_cache:
            cache.set(cache_key, tree, 3600)
        
        return tree
    
    @staticmethod
    def _build_tree_node(category: Category) -> Dict:
        """Construye un nodo del árbol recursivamente."""
        return {
            'id': category.id,
            'title': category.title,
            'slug': category.slug,
            'icon': category.icon,
            'description': category.description,
            'cat_image_url': category.cat_image.url if category.cat_image else None,
            'level': category.level,
            'parent_id': category.parent_id,
            'children': [
                CategoryService._build_tree_node(child) 
                for child in category.get_children()
            ]
        }
    
    @staticmethod
    def get_breadcrumb(category: Category) -> List[Category]:
        """
        Obtiene el breadcrumb (ruta) de una categoría.
        
        Returns:
            Lista ordenada desde raíz hasta la categoría actual
        """
        ancestors = list(category.get_ancestors())
        return ancestors + [category]
    
    @staticmethod
    def get_siblings(category: Category, include_self: bool = False) -> List[Category]:
        """Obtiene las categorías hermanas."""
        return list(category.get_siblings(include_self=include_self))
    
    @staticmethod
    def get_category_path(category: Category) -> str:
        """
        Obtiene la ruta completa como string.
        
        Returns:
            String como "Electrónica > Celulares > Smartphones"
        """
        breadcrumb = CategoryService.get_breadcrumb(category)
        return ' > '.join([cat.title for cat in breadcrumb])
    
    # ===========================================================================
    # MÉTODOS DE CREACIÓN Y MODIFICACIÓN
    # ===========================================================================
    
    @staticmethod
    @transaction.atomic
    def create_category(
        title: str,
        slug: Optional[str] = None,
        parent_id: Optional[int] = None,
        icon: Optional[str] = None,
        description: Optional[str] = None,
        cat_image = None
    ) -> Tuple[Category, Optional[str]]:
        """
        Crea una nueva categoría con validaciones.
        
        Returns:
            Tuple (categoría creada, error si hay)
        """
        # Validar título
        if not title or len(title.strip()) == 0:
            return None, "El título es requerido"
        
        title = title.strip()
        
        # Generar slug si no se proporciona
        if not slug:
            slug = slugify(title)
        else:
            slug = slugify(slug)
        
        # Validar slug único
        if Category.objects.filter(slug=slug).exists():
            return None, f"El slug '{slug}' ya existe"
        
        # Validar padre si se proporciona
        parent = None
        if parent_id:
            try:
                parent = Category.objects.get(id=parent_id)
            except Category.DoesNotExist:
                return None, f"La categoría padre con ID {parent_id} no existe"
        
        # Crear categoría
        try:
            category = Category.objects.create(
                title=title,
                slug=slug,
                parent=parent,
                icon=icon,
                description=description or '',
                cat_image=cat_image
            )
            
            # Invalidar caché
            CategoryService.clear_cache()
            
            return category, None
            
        except Exception as e:
            return None, f"Error al crear categoría: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def update_category(
        category_id: int,
        title: Optional[str] = None,
        slug: Optional[str] = None,
        parent_id: Optional[int] = None,
        icon: Optional[str] = None,
        description: Optional[str] = None,
        cat_image = None
    ) -> Tuple[Optional[Category], Optional[str]]:
        """
        Actualiza una categoría existente.
        
        Returns:
            Tuple (categoría actualizada, error si hay)
        """
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return None, "Categoría no encontrada"
        
        # Actualizar título
        if title is not None:
            title = title.strip()
            if len(title) == 0:
                return None, "El título no puede estar vacío"
            category.title = title
        
        # Actualizar slug
        if slug is not None:
            slug = slugify(slug)
            # Verificar que sea único (excepto para la misma categoría)
            if Category.objects.filter(slug=slug).exclude(id=category_id).exists():
                return None, f"El slug '{slug}' ya existe"
            category.slug = slug
        
        # Actualizar padre
        if parent_id is not None:
            if parent_id == 0:
                category.parent = None
            else:
                try:
                    parent = Category.objects.get(id=parent_id)
                    
                    # Validar que no se mueva a sí misma o a un descendiente
                    if parent == category or parent in category.get_descendants():
                        return None, "No se puede mover a sí misma o a un descendiente"
                    
                    category.parent = parent
                except Category.DoesNotExist:
                    return None, f"La categoría padre con ID {parent_id} no existe"
        
        # Actualizar otros campos
        if icon is not None:
            category.icon = icon
        
        if description is not None:
            category.description = description
        
        if cat_image is not None:
            category.cat_image = cat_image
        
        try:
            category.save()
            
            # Invalidar caché
            CategoryService.clear_cache()
            
            return category, None
            
        except Exception as e:
            return None, f"Error al actualizar: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def delete_category(category_id: int, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Elimina una categoría.
        
        Args:
            category_id: ID de la categoría
            force: Si es True, elimina aunque tenga hijos (CASCADE)
        
        Returns:
            Tuple (éxito, error si hay)
        """
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return False, "Categoría no encontrada"
        
        # Verificar si tiene hijos
        if not force and category.get_children().exists():
            return False, "La categoría tiene subcategorías. Usa force=True para eliminar todo el subárbol"
        
        # Verificar si tiene productos (si aplica)
        # if hasattr(category, 'products') and category.products.exists():
        #     return False, "La categoría tiene productos asociados"
        
        try:
            category.delete()
            
            # Invalidar caché
            CategoryService.clear_cache()
            
            return True, None
            
        except Exception as e:
            return False, f"Error al eliminar: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def move_category(
        category_id: int,
        new_parent_id: Optional[int] = None,
        position: str = 'last-child'
    ) -> Tuple[Optional[Category], Optional[str]]:
        """
        Mueve una categoría a un nuevo padre.
        
        Args:
            category_id: ID de la categoría a mover
            new_parent_id: ID del nuevo padre (None = raíz)
            position: 'first-child', 'last-child', 'left', 'right'
        
        Returns:
            Tuple (categoría movida, error si hay)
        """
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return None, "Categoría no encontrada"
        
        # Mover a raíz
        if new_parent_id is None or new_parent_id == 0:
            category.parent = None
            category.save()
            CategoryService.clear_cache()
            return category, None
        
        # Mover a otro padre
        try:
            new_parent = Category.objects.get(id=new_parent_id)
        except Category.DoesNotExist:
            return None, "Categoría padre no encontrada"
        
        # Validar que no se mueva a sí misma o a un descendiente
        if new_parent == category or new_parent in category.get_descendants():
            return None, "No se puede mover a sí misma o a un descendiente"
        
        try:
            category.move_to(new_parent, position)
            CategoryService.clear_cache()
            return category, None
            
        except Exception as e:
            return None, f"Error al mover: {str(e)}"
    
    # ===========================================================================
    # OPERACIONES MASIVAS
    # ===========================================================================
    
    @staticmethod
    @transaction.atomic
    def create_bulk_categories(categories_data: List[Dict]) -> Tuple[List[Category], List[str]]:
        """
        Crea múltiples categorías en una sola transacción.
        
        Args:
            categories_data: Lista de diccionarios con datos de categorías
        
        Returns:
            Tuple (categorías creadas, errores)
        """
        created_categories = []
        errors = []
        
        for idx, data in enumerate(categories_data):
            category, error = CategoryService.create_category(**data)
            
            if category:
                created_categories.append(category)
            else:
                errors.append(f"Categoría {idx + 1}: {error}")
        
        return created_categories, errors
    
    @staticmethod
    @transaction.atomic
    def rebuild_tree() -> bool:
        """
        Reconstruye el árbol MPTT.
        Útil si hay inconsistencias.
        
        Returns:
            True si fue exitoso
        """
        try:
            Category.objects.rebuild()
            CategoryService.clear_cache()
            return True
        except Exception:
            return False
    
    # ===========================================================================
    # ESTADÍSTICAS Y ANÁLISIS
    # ===========================================================================
    
    @staticmethod
    def get_statistics() -> Dict:
        """
        Obtiene estadísticas completas del sistema de categorías.
        
        Returns:
            Diccionario con estadísticas
        """
        total = Category.objects.count()
        
        if total == 0:
            return {
                'total_categories': 0,
                'root_categories': 0,
                'leaf_categories': 0,
                'max_depth': 0,
                'levels': {},
                'avg_children': 0
            }
        
        root_count = Category.objects.filter(level=0).count()
        leaf_count = Category.objects.filter(children__isnull=True).count()
        
        # Distribución por nivel
        levels = {}
        max_level = 0
        for level in range(10):  # Máximo 10 niveles
            count = Category.objects.filter(level=level).count()
            if count > 0:
                levels[f'level_{level}'] = count
                max_level = level
        
        # Promedio de hijos por categoría
        categories_with_children = Category.objects.annotate(
            children_count=Count('children')
        ).filter(children_count__gt=0)
        
        if categories_with_children.exists():
            avg_children = sum(c.children_count for c in categories_with_children) / categories_with_children.count()
        else:
            avg_children = 0
        
        return {
            'total_categories': total,
            'root_categories': root_count,
            'leaf_categories': leaf_count,
            'max_depth': max_level,
            'levels': levels,
            'avg_children': round(avg_children, 2),
            'categories_with_children': categories_with_children.count()
        }
    
    @staticmethod
    def get_category_stats(category: Category) -> Dict:
        """
        Obtiene estadísticas de una categoría específica.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'id': category.id,
            'title': category.title,
            'level': category.level,
            'children_count': category.get_children().count(),
            'descendants_count': category.get_descendant_count(),
            'siblings_count': category.get_siblings().count(),
            'is_leaf': not category.get_children().exists(),
            'is_root': category.level == 0,
            'path': CategoryService.get_category_path(category),
            # 'products_count': category.products.count() if hasattr(category, 'products') else 0
        }
    
    # ===========================================================================
    # VALIDACIONES
    # ===========================================================================
    
    @staticmethod
    def validate_slug(slug: str, exclude_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Valida que un slug sea único y válido.
        
        Returns:
            Tuple (es válido, mensaje de error)
        """
        if not slug:
            return False, "El slug es requerido"
        
        slug = slugify(slug)
        
        if len(slug) == 0:
            return False, "El slug no puede estar vacío"
        
        query = Category.objects.filter(slug=slug)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        
        if query.exists():
            return False, f"El slug '{slug}' ya existe"
        
        return True, None
    
    @staticmethod
    def validate_parent(category_id: int, parent_id: int) -> Tuple[bool, Optional[str]]:
        """
        Valida que un padre sea válido para una categoría.
        
        Returns:
            Tuple (es válido, mensaje de error)
        """
        if category_id == parent_id:
            return False, "Una categoría no puede ser su propio padre"
        
        try:
            category = Category.objects.get(id=category_id)
            parent = Category.objects.get(id=parent_id)
        except Category.DoesNotExist:
            return False, "Categoría o padre no encontrado"
        
        if parent in category.get_descendants():
            return False, "No se puede mover a un descendiente"
        
        return True, None
    
    @staticmethod
    def can_delete(category: Category) -> Tuple[bool, Optional[str]]:
        """
        Verifica si una categoría puede ser eliminada.
        
        Returns:
            Tuple (puede eliminar, razón si no puede)
        """
        # Verificar hijos
        if category.get_children().exists():
            return False, "La categoría tiene subcategorías"
        
        # Verificar productos (si aplica)
        # if hasattr(category, 'products') and category.products.exists():
        #     return False, "La categoría tiene productos asociados"
        
        return True, None
    
    # ===========================================================================
    # CACHÉ
    # ===========================================================================
    
    @staticmethod
    def clear_cache():
        """Limpia toda la caché de categorías."""
        cache_keys = [
            'category_tree_None',
            'category_roots',
            'category_stats'
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        # Limpiar caché de árboles específicos
        for i in range(1, 100):  # Asumir máximo 100 categorías raíz
            cache.delete(f'category_tree_{i}')
    
    @staticmethod
    def warm_cache():
        """
        Pre-carga datos frecuentemente usados en caché.
        Útil para ejecutar después de modificaciones masivas.
        """
        # Pre-cargar árbol completo
        CategoryService.get_tree(use_cache=False)
        
        # Pre-cargar estadísticas
        stats = CategoryService.get_statistics()
        cache.set('category_stats', stats, 3600)
    
    # ===========================================================================
    # UTILIDADES
    # ===========================================================================
    
    @staticmethod
    def generate_unique_slug(title: str, category_id: Optional[int] = None) -> str:
        """
        Genera un slug único basado en el título.
        Si ya existe, agrega un número.
        
        Returns:
            Slug único
        """
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        
        while True:
            query = Category.objects.filter(slug=slug)
            if category_id:
                query = query.exclude(id=category_id)
            
            if not query.exists():
                return slug
            
            slug = f"{base_slug}-{counter}"
            counter += 1
    
    @staticmethod
    def export_to_dict(category: Category, include_children: bool = False) -> Dict:
        """
        Exporta una categoría a diccionario.
        
        Args:
            category: Categoría a exportar
            include_children: Incluir hijos recursivamente
        
        Returns:
            Diccionario con datos
        """
        data = {
            'id': category.id,
            'title': category.title,
            'slug': category.slug,
            'icon': category.icon,
            'description': category.description,
            'level': category.level,
            'parent_id': category.parent_id,
            'cat_image_url': category.cat_image.url if category.cat_image else None,
        }
        
        if include_children:
            data['children'] = [
                CategoryService.export_to_dict(child, include_children=True)
                for child in category.get_children()
            ]
        
        return data
    
    @staticmethod
    def import_from_dict(data: Dict, parent: Optional[Category] = None) -> Category:
        """
        Importa una categoría desde un diccionario.
        
        Args:
            data: Diccionario con datos
            parent: Categoría padre (opcional)
        
        Returns:
            Categoría creada
        """
        category = Category.objects.create(
            title=data['title'],
            slug=data.get('slug') or slugify(data['title']),
            icon=data.get('icon'),
            description=data.get('description', ''),
            parent=parent
        )
        
        # Importar hijos recursivamente
        for child_data in data.get('children', []):
            CategoryService.import_from_dict(child_data, parent=category)
        
        return category