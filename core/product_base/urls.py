
from django.urls import path , re_path, include
from .views import ListProductBaseViewAPIView , SingleProductBaseView, CategoryView, ListProductViewAPIView , SingleProductView , TagAutocompleteAPIView, PriceProductBaseView

urlpatterns = [
    path('product-base/<int:key>' , SingleProductBaseView.as_view(), name='get_product-base'),
    path('product-base/list' , ListProductBaseViewAPIView.as_view(), name='list-product-base'),
    path('category/list' , CategoryView.as_view(), name='list-category-all'),
    path('product-ins/list' , ListProductViewAPIView.as_view(), name='list-products'),
    path('product-ins/<int:key>' , SingleProductView.as_view(), name='get_product'),
    path('tag/autocompete', TagAutocompleteAPIView.as_view(), name='api-tag-autocomplete'),
    path('product-base/<int:id>/price' , PriceProductBaseView.as_view(), name='single_product_base_price'),
]