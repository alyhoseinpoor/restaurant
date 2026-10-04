from django.contrib import admin
from .models import Food , Category , Comment , Favorite , Order
@admin.register(Food)
class Foodadmin(admin.ModelAdmin):
    list_display=[
        "title",
        "desc",
        "price",
        "category",
        "img",
        "available",
    ]
    list_display_links=[
        "title",
    ]
    list_filter=[
        "category",
        "available",
    ]
    search_fields=[
        "title",
        "desc", 
    ]
    
@admin.register(Category)
class Categoryadmin(admin.ModelAdmin):
    list_display=[
        "name",
        "slug",
    ]
    list_display_links=[
        "name",
        "slug",
    ]

@admin.register(Comment)
class Commentadmin(admin.ModelAdmin):
    list_display=[
        "user",
        "food",
        "text",
        "created_at",
        "active",
    ]
    list_display_links=[
        "user",
        "food",
        "text",
        "created_at",
        "active",
    ]
    list_filter=[
        "active",
    ]

@admin.register(Favorite)
class Favoriteadmin(admin.ModelAdmin):
    list_display=[
        "user",
        "food",
    ]
    list_display_links=[
        "user",
        "food",
    ]
@admin.register(Order)
class Orderadmin(admin.ModelAdmin):
    list_display=[
        "number",
        "user",
        "food",
        "active",
    ]
    list_display_links=[
            "number",
    ]