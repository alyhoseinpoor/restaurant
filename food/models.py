from django.db import models
from django.contrib.auth import get_user_model
User=get_user_model()
# Create your models here.
class Food (models.Model):
    title=models.CharField(max_length=200,db_index=True)
    desc=models.TextField()
    price=models.IntegerField()
    category=models.ForeignKey('Category',on_delete=models.CASCADE)
    img=models.ImageField(upload_to="foods/",blank=True,null=True)
    available=models.BooleanField(default=True)
    slug=models.SlugField(unique=True,blank=True)
    class Meta:
        ordering = ['id']
    

class Category(models.Model):
    name=models.CharField(max_length=200)
    slug=models.SlugField(unique=True)
    img=models.ImageField(upload_to="categorys/",blank=True,null=True)
    class Meta:
        ordering = ['id']
    def __str__(self):
        return self.name
    
class Comment(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,)
    food=models.ForeignKey('Food',on_delete=models.CASCADE)
    text=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    active=models.BooleanField(default=False)
    class Meta:
        ordering = ['created_at']

class Favorite(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,)
    food=models.ForeignKey('Food',on_delete=models.CASCADE)
    class Meta:
        ordering = ['id']
        unique_together = ('user','food')

class Order (models.Model):
    number=models.IntegerField(default=0)
    user=models.ForeignKey(User,on_delete=models.CASCADE,)
    food=models.ForeignKey('Food',on_delete=models.CASCADE)
    active=models.BooleanField(default=False)#هر زمان سفارش نهایی شد این فعال میشه و غیر فعال به معنی مانددن در سبد خرید است
    class Meta:
        ordering = ['id']