from django.contrib import admin

from .models import Category, Comment, Favorite, Food, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'available']
    list_editable = ['price', 'available']
    list_filter = ['available', 'category']
    search_fields = ['title', 'desc']
    list_select_related = ['category']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'food', 'active', 'created_at']
    list_filter = ['active']
    list_select_related = ['user', 'food']
    actions = ['approve']

    @admin.action(description='Approve selected comments')
    def approve(self, request, queryset):
        queryset.update(active=True)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'food']
    list_select_related = ['user', 'food']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ['food']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total', 'created_at', 'placed_at']
    list_filter = ['status']
    list_select_related = ['user']
    inlines = [OrderItemInline]
    actions = ['mark_preparing', 'mark_delivered']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')

    @admin.display(description='Total')
    def total(self, obj):
        return obj.total

    @admin.action(description='Mark selected placed orders as preparing')
    def mark_preparing(self, request, queryset):
        queryset.filter(status=Order.Status.PLACED).update(status=Order.Status.PREPARING)

    @admin.action(description='Mark selected preparing orders as delivered')
    def mark_delivered(self, request, queryset):
        queryset.filter(status=Order.Status.PREPARING).update(status=Order.Status.DELIVERED)
