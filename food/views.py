from django.db import transaction
from django.db.models import ProtectedError, prefetch_related_objects
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from . import serializers
from .filters import FoodFilter
from .models import MAX_QUANTITY, Category, Comment, Favorite, Food, Order, OrderItem
from .permissions import IsAdminOrReadOnly, IsOwner


def get_cart(user):
    """Return the user's open cart, creating it on first use."""
    cart, _ = Order.objects.get_or_create(user=user, status=Order.Status.CART)
    return cart


class ProtectedDeleteMixin:
    """Turn a ProtectedError (500) into a readable 400 response."""

    protected_message = 'This object is still in use and cannot be deleted.'

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError({'detail': self.protected_message}) from None


# ---------- Auth ----------
class RegisterView(CreateAPIView):
    serializer_class = serializers.RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


# ---------- Menu ----------
class CategoryViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    protected_message = 'This category still has foods; move or delete them first.'


class FoodViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Food.objects.select_related('category')
    serializer_class = serializers.FoodSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FoodFilter
    search_fields = ['title', 'desc']
    ordering_fields = ['price', 'title']
    protected_message = 'This food was ordered before; mark it as unavailable instead of deleting it.'


# ---------- Comments & favorites ----------
class CommentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Approved comments are public; new comments wait for admin approval."""

    queryset = Comment.objects.filter(active=True).select_related('user', 'food')
    serializer_class = serializers.CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['food']
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'comment'

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FavoriteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.FavoriteSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('food')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---------- Cart ----------
class CartView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'order'

    @extend_schema(responses=serializers.OrderSerializer)
    def get(self, request):
        cart = get_cart(request.user)
        prefetch_related_objects([cart], 'items__food')
        return Response(serializers.OrderSerializer(cart).data)

    @extend_schema(responses={204: None})
    def delete(self, request):
        """Empty the cart."""
        get_cart(request.user).items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Add, change the quantity of, or remove items in the current user's cart."""

    serializer_class = serializers.OrderItemSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'patch', 'delete', 'head', 'options']
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'order'

    def get_queryset(self):
        return OrderItem.objects.filter(
            order__user=self.request.user,
            order__status=Order.Status.CART,
        ).select_related('food')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        food = serializer.validated_data['food']
        quantity = serializer.validated_data['quantity']

        item, created = OrderItem.objects.get_or_create(
            order=get_cart(request.user),
            food=food,
            defaults={'quantity': quantity, 'unit_price': food.price},
        )
        if not created:
            if item.quantity + quantity > MAX_QUANTITY:
                raise ValidationError({'quantity': f'You can order at most {MAX_QUANTITY} of one food.'})
            item.quantity += quantity
            item.unit_price = food.price
            item.save(update_fields=['quantity', 'unit_price'])

        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(self.get_serializer(item).data, status=code)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'order'

    @extend_schema(request=None, responses={201: serializers.OrderSerializer})
    def post(self, request):
        """Turn the cart into a placed order, re-pricing items at the current menu price."""
        with transaction.atomic():
            cart = (
                Order.objects.select_for_update()
                .filter(user=request.user, status=Order.Status.CART)
                .first()
            )
            items = list(cart.items.select_related('food')) if cart else []
            if not items:
                raise ValidationError({'detail': 'Your cart is empty.'})

            unavailable = [item.food.title for item in items if not item.food.available]
            if unavailable:
                raise ValidationError(
                    {'detail': 'These foods are no longer available: ' + ', '.join(unavailable)}
                )

            for item in items:
                item.unit_price = item.food.price
            OrderItem.objects.bulk_update(items, ['unit_price'])

            cart.status = Order.Status.PLACED
            cart.placed_at = timezone.now()
            cart.save(update_fields=['status', 'placed_at'])

        prefetch_related_objects([cart], 'items__food')
        return Response(serializers.OrderSerializer(cart).data, status=status.HTTP_201_CREATED)


# ---------- Orders ----------
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Order history of the current user (the open cart is not listed here)."""

    serializer_class = serializers.OrderSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'order'

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .exclude(status=Order.Status.CART)
            .prefetch_related('items__food')
        )

    @extend_schema(request=None, responses=serializers.OrderSerializer)
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order that has been placed but not yet prepared."""
        order = self.get_object()
        if order.status != Order.Status.PLACED:
            raise ValidationError({'detail': 'Only orders in the "placed" state can be cancelled.'})
        order.status = Order.Status.CANCELLED
        order.save(update_fields=['status'])
        return Response(self.get_serializer(order).data)
