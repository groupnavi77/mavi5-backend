from django.db import models
from django.utils.timesince import timesince
from core.product_ins.models import Product
from core.product_base.models import ProductBase



class ReviewProductBase(models.Model):
    product = models.ForeignKey(ProductBase, on_delete=models.CASCADE, related_name='product_base_reviews')
    rating = models.IntegerField()
    author = models.CharField(max_length=200)
    text = models.TextField()
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def FORMAT(self):
        return timesince(self.created_at)

    def approve(self):
        self.approved_comment = True
        self.save()

    def __str__(self):
        return self.text
    
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.IntegerField()
    author = models.CharField(max_length=200)
    text = models.TextField()
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def FORMAT(self):
        return timesince(self.created_at)

    def approve(self):
        self.approved_comment = True
        self.save()

    def __str__(self):
        return self.text