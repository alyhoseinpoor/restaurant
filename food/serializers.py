from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import MAX_QUANTITY, Category, Comment, Favorite, Food, Order, OrderItem

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'img']


class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = ['id', 'title', 'desc', 'price', 'category', 'img', 'available', 'slug']


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'food', 'username', 'text', 'created_at', 'active']
        # `active` is controlled by admins (moderation), never by the author.
        read_only_fields = ['created_at', 'active']


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'food']

    def validate_food(self, food):
        user = self.context['request'].user
        if Favorite.objects.filter(user=user, food=food).exists():
            raise serializers.ValidationError('This food is already in your favorites.')
        return food


class OrderItemSerializer(serializers.ModelSerializer):
    food_title = serializers.CharField(source='food.title', read_only=True)
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_QUANTITY, default=1)
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'food', 'food_title', 'quantity', 'unit_price', 'subtotal']
        read_only_fields = ['unit_price']

    def validate_food(self, food):
        if not food.available:
            raise serializers.ValidationError('This food is currently unavailable.')
        return food

    def validate(self, attrs):
        if self.instance is not None and 'food' in attrs and attrs['food'] != self.instance.food:
            raise serializers.ValidationError(
                {'food': 'The food of an item cannot be changed; remove it and add another.'}
            )
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'items', 'total', 'created_at', 'placed_at']
        read_only_fields = fields
