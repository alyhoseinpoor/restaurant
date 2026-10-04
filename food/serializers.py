from rest_framework.serializers import ModelSerializer
from .models import Food , Order , Category , Comment ,Favorite
class FoodSerializer(ModelSerializer):
    class Meta:
        model = Food
        fields = ['id', 'title', 'desc', 'price', 'category', 'img', 'available', 'slug']

class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'img']

class OrderSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'food', 'number', 'active']
        read_only_fields = ['active']  # فقط از طریق اکشن finalize باید تغییر کنه، نه مستقیم POST/PUT

class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'food', 'text', 'created_at', 'active']
        read_only_fields = ['created_at', 'active']  # active رو فقط ادمین باید بتونه عوض کنه

class FavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'food']