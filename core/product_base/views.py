from django.shortcuts import render
from django.core.cache import cache
from django.db.models import Count, Q , F
from rest_framework import generics ,pagination, generics , response , status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view , parser_classes, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound

from django_filters.rest_framework import DjangoFilterBackend ,FilterSet
from rest_framework.filters import OrderingFilter,SearchFilter

from django.http import Http404 


from core.product.serializers import ProductBaseSerializer , CategorySerializer , SingleProductBaseSerializer,ProductSerializer,SingleProductSerializer , TagAutocompleteSerializer , PriceSerializerProductBase, PriceSerializer
from core.product.models import Product  , Category  , Image , ProductBase, Review, ReviewProductBase, ImageProductBase, Price,Discount

from taggit.models import Tag

# Create your views here.

class CustomPagination(pagination.PageNumberPagination):
    page_size = 60
    page_size_query_param = 'per_page'
    
    def get_paginated_response(self, data):
        return response.Response({
            'page_size_default': self.page_size,
            'total_objects': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page_number': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })


#SECCION PRODUCTOS BASE
class ListProductBaseViewAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductBaseSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['description']
    filterset_fields = {'category__slug': ['icontains'],}


    def get_queryset(self):
        return ProductBase.objects.filter(published=True).order_by('-created_at')

class SingleProductBaseView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SingleProductBaseSerializer

    def get_queryset(self):
        uuid = self.kwargs['key']
        queryset = ProductBase.objects.filter(key=uuid)
        if not queryset.exists():
            raise NotFound("Product not found")
        return queryset
    
class PriceProductBaseView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PriceSerializer  # Cambiamos al serializador directo de Price
    
    def get_queryset(self):
        product_id = self.kwargs['id']
        return Price.objects.filter(product_id=product_id)
    
#SECCION PRODUCTOS
class ListProductViewAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['description']
    filterset_fields = {'Product_base__key': ['icontains'],'tag__slug': ['in'],}


    def get_queryset(self):
        return Product.objects.filter(published=True).order_by('-created_at')

class SingleProductView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SingleProductSerializer

    def get_queryset(self):
        uuid = self.kwargs['key']
        queryset = Product.objects.filter(key=uuid)
        if not queryset.exists():
            raise NotFound("Product not found")
        return queryset

#SECCION CATEGORIAS
class CategoryView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = {'slug': ['icontains'],}
    def get_queryset(self):
        queryset = Category.objects.filter(level=0)
        return queryset


class TagAutocompleteAPIView(generics.ListAPIView):
    # La consulta base incluye todas las etiquetas
    permission_classes = [AllowAny]
    queryset = Tag.objects.all() 
    serializer_class = TagAutocompleteSerializer
    
    # Usamos el backend de filtro de búsqueda de DRF
    filter_backends = [SearchFilter]
    
    # 🌟 Definimos que la búsqueda solo se aplique al campo 'name' de la etiqueta
    search_fields = ['name'] 
    
    # Opcional: limita el queryset para aumentar la velocidad (e.g., solo 20 resultados)
    # pagination_class = YourLimitPaginationClass

