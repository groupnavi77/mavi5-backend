from django.contrib import admin
from django import forms
from django.urls import reverse_lazy
from .models import  ProductBase, ImageProductBase , Price,Discount
from core.category.models import Category
from core.product_ins.models import Product , Image
from core.review.models import ReviewProductBase , Review
from mptt.admin import DraggableMPTTAdmin

# --- WIDGET PERSONALIZADO ---

class HashtagAutocompleteWidget(forms.TextInput):
    # La plantilla base del admin
    template_name = 'django/forms/widgets/input.html'
    
    # 🌟 Atributo clave: Inyecta el archivo JS en el formulario
    @property
    def media(self):
        # El archivo JS debe estar en static/admin/js/hashtag-admin.js
        return forms.Media(
            js=[
                'admin/js/core.js',          # Dependencia obligatoria en Django Admin
                'admin/js/jquery.init.js',   # Asegura que $ sea alias de django.jQuery
                'admin-static/js/hashtag-admin.js'  # Tu script
            ]
        )
    # 🌟 CORRECCIÓN CLAVE 🌟
    def format_value(self, value):
        """
        Convierte la lista/manager de objetos Tag en una cadena separada por comas 
        (formato que taggit espera para la edición).
        """
        if isinstance(value, str):
            return value
        
        if not value:
            return ''
        
        tags_to_join = None

        # 1. Obtener la colección de Tags
        if hasattr(value, 'all'):
            # TaggableManager o QuerySet
            tags_to_join = value.all()
        elif hasattr(value, '__iter__'):
            # Lista (cuando falla la validación)
            tags_to_join = value
        
        if tags_to_join is not None:
            # 🌟 CORRECCIÓN CLAVE 🌟: Unir los nombres de tags con ', '
            # Esto es lo que Taggit necesita para parsear la entrada.
            # NO añadimos el # aquí, porque el usuario debe poder escribirlo, 
            # y Taggit ignora los caracteres de puntuación.
            return ', '.join(tag.name for tag in tags_to_join)
            
        return value # Devuelve el valor original si no es reconocido

class PriceAdmin(admin.TabularInline):

    model = Price
    extra = 1   

class DiscountAdmin(admin.TabularInline):

    model = Discount
    extra = 1

# --- CLASES INLINE Y ADMIN BASE ---
class MediaProductAdmin(admin.TabularInline):
    model = Image
    extra = 1

class MediaProductBaseAdmin(admin.TabularInline):
    model = ImageProductBase
    extra = 1

class ProductBaseAdmin(admin.ModelAdmin):
    list_display = ('title' , 'published')
    prepopulated_fields = {'slug':('title',)}
    inlines = [MediaProductBaseAdmin , PriceAdmin , DiscountAdmin]

class ProductAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'published')
    inlines = [MediaProductAdmin]
    
    # Sobreescribimos el campo 'tags' para usar el Widget personalizado
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # El campo 'tags' es de 'django-taggit', y se identifica por su nombre.
        if db_field.name == 'tag':
            # 1. Obtenemos la URL de la API de autocompletado
            autocomplete_url = '/api/tags/autocomplete'
            
            # 2. Reemplazamos el widget de tags con el nuestro
            kwargs['widget'] = HashtagAutocompleteWidget(
                # Pasamos la URL al widget como un atributo de datos HTML
                attrs={'data-autocomplete-url': autocomplete_url,'class': 'vTextField'}
                
            )
        
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
admin.site.register( 
    Category,   
    DraggableMPTTAdmin,
    
    list_display=(
        'tree_actions',
        'indented_title',
        # ...more fields if you feel like it...
    ),
    prepopulated_fields = {'slug':('title',)},
    list_display_links=(
        'indented_title',
    ),)

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductBase, ProductBaseAdmin)