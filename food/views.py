from rest_framework.viewsets import ModelViewSet
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.permissions import IsAdminUser, AllowAny
from .models import Food, Category, Comment, Order, Favorite
from . import serializers
from .permision import IsOwner


#FOOD_API
class FoodViewSet(ModelViewSet):
    queryset = Food.objects.select_related('category').all()
    serializer_class = serializers.FoodSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'desc']
    ordering_fields = ['price']

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')

        if category:
            queryset = queryset.filter(category__slug=category)

        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


# CATEGORY_API
class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

# COMMENT_API
class CommentListCreate(generics.ListCreateAPIView):
    queryset = Comment.objects.filter(active=True).select_related('user','food')
    serializer_class = serializers.CommentSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'comment'

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



# ORDER_API
class OrderViewSet(ModelViewSet):
    queryset=Order.objects.all()
    serializer_class = serializers.OrderSerializer
    permission_classes = [IsAuthenticated,IsOwner]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('user','food')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # increase_quantity
    @action(detail=True, methods=['post'])
    def increase(self, request, pk=None):
        order = self.get_object()
        order.number += 1
        order.save()
        return Response({'status': 'increased'})

    # decrease_quantity
    @action(detail=True, methods=['post'])
    def decrease(self, request, pk=None):
        order = self.get_object()

        if order.number > 1:
            order.number -= 1
            order.save()
        else:
            order.delete()

        return Response({'status': 'updated'})

    # finalize_order
    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        order = self.get_object()
        order.active = True
        order.save()
        return Response({'status': 'finalized'})

    # delete_order
    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        order = self.get_object()
        order.delete()
        return Response({'status': 'deleted'})

# FAVORITE_API
class FavoriteListCreate(generics.ListCreateAPIView):
    serializer_class = serializers.FavoriteSerializer
    permission_classes = [IsAuthenticated,IsOwner]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('food')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)