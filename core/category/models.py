from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

class Category(MPTTModel):
    title = models.CharField(max_length=50, unique=False)
    slug = models.SlugField(max_length=100, unique=True, null=True)
    icon = models.CharField(max_length=255 , blank=True , null=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='images/categories', blank=True)
    
    

    class Meta:
        verbose_name='category'
        verbose_name_plural='categories'
    class MPTTMeta:
        order_insertion_by = ['title']
            
    def __str__(self):
        return self.title
