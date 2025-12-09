from rest_framework import serializers
from easy_thumbnails_rest.serializers import ThumbnailerSerializer
from easy_thumbnails.templatetags.thumbnail import thumbnail_url
from core.product.models import Product  , Category, Image , ProductBase, Review, ReviewProductBase, ImageProductBase , Price,Discount
from core.user.models import UserAccount as User
from taggit.serializers import TaggitSerializer, TagListSerializerField
from taggit.models import Tag

class ThumbnailSerializer(serializers.ImageField):
    """ Serializer for thumbnail creation using easy-thumbnails (Needed when using Django Rest Framework) """
    def __init__(self, alias, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read_only = True
        self.alias = alias

    def to_representation(self, value):
        if not value:
            return None

        url = thumbnail_url(value, self.alias)
        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)

        return url
    
#PRICE SERIALIZERS
class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = ('__all__')
    
#USER SERIALIZERS

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

#CATEGORY SERIALIZERS
class CategorySerializerModel(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('__all__')

class CategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields = ('__all__')
        
    def get_fields(self):
        fields = super(CategorySerializer, self).get_fields()
        fields['children'] = CategorySerializer(many=True, required=False)
        return fields
    
#PRODUCT BASE SERIALIZERS

class ImageSerializerProductBase(serializers.ModelSerializer):
    image = ThumbnailerSerializer(alias='img316')
    class Meta:
        model = ImageProductBase
        fields = ('id','image')

class ImageSerializerSingleProductBase(serializers.ModelSerializer):
    image = ThumbnailerSerializer(alias='img800')
    class Meta:
        model = ImageProductBase
        fields = ('id','image')


class ProductBaseSerializer(TaggitSerializer, serializers.ModelSerializer):
    tag = TagListSerializerField()
    image = ThumbnailerSerializer(alias='img316')
    category = CategorySerializerModel(many=False, read_only=True)
    
    class Meta:
        model = ProductBase
        fields = ("id","key","title","slug","category","image","tag")


class SingleProductBaseSerializer(TaggitSerializer, serializers.ModelSerializer):
    tag = TagListSerializerField()
    category = CategorySerializerModel(many=False, read_only=True)
    image_list = ImageSerializerSingleProductBase(many=True, read_only=True , source='product_base_images')
    image = ThumbnailerSerializer(alias='img800')
    class Meta:
        model = ProductBase
        fields = ("id","key","title","slug","short_description","description","category","image","image_list","tag")

class PriceSerializerProductBase(serializers.ModelSerializer):
    advanced_prices = PriceSerializer(many=True, read_only=True , source='product_base_prices')
    class Meta:
        model = ProductBase
        fields = ('id','advanced_prices')

#PRODUCT SERIALIZERS
class ImageSerializer(serializers.ModelSerializer):
    image = ThumbnailerSerializer(alias='img316')
    class Meta:
        model = Image
        fields = ('id','image')
        
class ImageSerializerSingleProduct(serializers.ModelSerializer):
    image = ThumbnailerSerializer(alias='img800')
    class Meta:
        model = Image
        fields = ('id','image')

class ProductSerializer(TaggitSerializer, serializers.ModelSerializer):
    tag = TagListSerializerField()
    image = ThumbnailerSerializer(alias='img316')
    product_base = ProductBaseSerializer(many=False, read_only=True)
    
    class Meta:
        model = Product
        fields = ("id","key","description","image","product_base","tag")

class SingleProductSerializer(TaggitSerializer, serializers.ModelSerializer):
    tag = TagListSerializerField()
    product_base = ProductBaseSerializer(many=False, read_only=True)
    image_list = ImageSerializerSingleProduct(many=True, read_only=True , source='product_images')
    image = ThumbnailerSerializer(alias='img800')
    user = UserSerializer(many=False, read_only=True)
    class Meta:
        model = Product
        fields = ("id","key","description","image","image_list","product_base","tag","created_at","updated_at","user")

class TagAutocompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        # Solo necesitamos el ID (para referencia) y el nombre (para mostrar/buscar)
        fields = ['id', 'name']