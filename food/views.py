from django.db import transaction
from django.db.models import ProtectedError, prefetch_related_objects
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import serializers
from .filters import FoodFilter
from .models import MAX_QUANTITY, Category, Comment, Favorite, Food, Order, OrderItem
from .permissions import IsAdminOrReadOnly, IsOwner

# Swagger UI groups operations by these tags (see SPECTACULAR_SETTINGS['TAGS']).
AUTH, MENU, CART, ORDERS, COMMENTS, FAVORITES = 'Auth', 'Menu', 'Cart', 'Orders', 'Comments', 'Favorites'


def op(tag, summary, description=None, **kwargs):
    """Shortcut for an @extend_schema with a tag, a summary and a description."""
    return extend_schema(tags=[tag], summary=summary, description=description, **kwargs)


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
@extend_schema_view(
    post=op(
        AUTH,
        'Register',
        'Create a new account. Afterwards call **Log in** to get a token.',
        responses={
            201: serializers.RegisterSerializer,
            400: OpenApiResponse(description='Validation error: weak password or username already taken.'),
        },
        examples=[
            OpenApiExample(
                'New user',
                value={'username': 'ali', 'email': 'ali@example.com', 'password': 'Str0ng-Pass!word'},
                request_only=True,
            )
        ],
    )
)
class RegisterView(CreateAPIView):
    serializer_class = serializers.RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'


@extend_schema_view(
    post=op(
        AUTH,
        'Log in (get JWT tokens)',
        'Returns a short-lived `access` token (60 minutes) and a `refresh` token (1 day). '
        'Send the access token as `Authorization: Bearer <access>`; in Swagger UI click **Authorize** and paste it.',
        examples=[OpenApiExample('Credentials', value={'username': 'ali', 'password': 'Str0ng-Pass!word'}, request_only=True)],
    )
)
class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


@extend_schema_view(
    post=op(AUTH, 'Refresh the access token', 'Exchange a valid `refresh` token for a new `access` token.')
)
class RefreshView(TokenRefreshView):
    pass


# ---------- Menu ----------
@extend_schema_view(
    list=op(MENU, 'List categories', 'Public. Paginated (10 per page, `?page=2`).'),
    retrieve=op(MENU, 'Category detail', 'Public.'),
    create=op(MENU, 'Create a category', 'Staff only.'),
    update=op(MENU, 'Replace a category', 'Staff only.'),
    partial_update=op(MENU, 'Update a category', 'Staff only.'),
    destroy=op(
        MENU,
        'Delete a category',
        'Staff only. Returns 400 while the category still has foods.',
    ),
)
class CategoryViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    protected_message = 'This category still has foods; move or delete them first.'


@extend_schema_view(
    list=op(
        MENU,
        'List foods',
        'Public and paginated. Filter by `category` (slug), `available`, `min_price`, `max_price`; '
        'search in title and description with `search`; sort with `ordering` (`price`, `-price`, `title`).',
    ),
    retrieve=op(MENU, 'Food detail', 'Public.'),
    create=op(MENU, 'Create a food', 'Staff only. The slug is generated from the title when omitted.'),
    update=op(MENU, 'Replace a food', 'Staff only.'),
    partial_update=op(MENU, 'Update a food', 'Staff only.'),
    destroy=op(
        MENU,
        'Delete a food',
        'Staff only. Returns 400 if the food was ordered before; mark it `available: false` instead.',
    ),
)
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
@extend_schema_view(
    list=op(
        COMMENTS,
        'List approved comments',
        'Public. Only comments approved by an admin are returned. Use `?food=<id>` to get the comments of one food.',
    ),
    create=op(
        COMMENTS,
        'Create a comment',
        'Requires login. The comment stays hidden (`active: false`) until an admin approves it.',
    ),
)
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


@extend_schema_view(
    list=op(FAVORITES, 'List my favorites', 'Only the favorites of the logged-in user.'),
    create=op(
        FAVORITES,
        'Add a favorite',
        'Returns 400 if the food is already in your favorites.',
    ),
    destroy=op(FAVORITES, 'Remove a favorite', 'Only your own favorites can be removed (others return 404).'),
)
class FavoriteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.FavoriteSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # schema generation has no real user
            return Favorite.objects.none()
        return Favorite.objects.filter(user=self.request.user).select_related('food')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---------- Cart ----------
class CartView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'order'

    @extend_schema(
        tags=[CART],
        summary='View my cart',
        description='The open cart of the logged-in user with its items and the server-side total. '
        'It is created automatically on first use.',
        responses=serializers.OrderSerializer,
    )
    def get(self, request):
        cart = get_cart(request.user)
        prefetch_related_objects([cart], 'items__food')
        return Response(serializers.OrderSerializer(cart).data)

    @extend_schema(tags=[CART], summary='Empty the cart', description='Remove all items from the cart.', responses={204: None})
    def delete(self, request):
        """Empty the cart."""
        get_cart(request.user).items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    create=op(
        CART,
        'Add a food to the cart',
        'Adds the food with the current menu price. If the food is already in the cart its quantity '
        f'increases (200 instead of 201). Quantity must be between 1 and {MAX_QUANTITY}.',
        responses={
            201: serializers.OrderItemSerializer,
            200: OpenApiResponse(
                response=serializers.OrderItemSerializer,
                description='The food was already in the cart; its quantity was increased.',
            ),
            400: OpenApiResponse(description='Invalid quantity, or the food is unavailable.'),
        },
        examples=[OpenApiExample('Two portions', value={'food': 1, 'quantity': 2}, request_only=True)],
    ),
    partial_update=op(
        CART,
        'Change the quantity of a cart item',
        'Only items of your own open cart can be changed (others return 404).',
        examples=[OpenApiExample('New quantity', value={'quantity': 3}, request_only=True)],
    ),
    destroy=op(CART, 'Remove an item from the cart', 'Only items of your own open cart can be removed.'),
)
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
        if getattr(self, 'swagger_fake_view', False):  # schema generation has no real user
            return OrderItem.objects.none()
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

    @extend_schema(
        tags=[CART],
        summary='Checkout: place the order',
        description='Turns the cart into an order with status `placed`. Items are re-priced at the current '
        'menu price inside a database transaction.',
        request=None,
        responses={
            201: serializers.OrderSerializer,
            400: OpenApiResponse(description='The cart is empty, or a food is no longer available.'),
        },
    )
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
@extend_schema_view(
    list=op(ORDERS, 'List my orders', 'Order history of the logged-in user. The open cart is not included.'),
    retrieve=op(ORDERS, 'Order detail', 'Only your own orders (others return 404).'),
)
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Order history of the current user (the open cart is not listed here)."""

    serializer_class = serializers.OrderSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'order'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # schema generation has no real user
            return Order.objects.none()
        return (
            Order.objects.filter(user=self.request.user)
            .exclude(status=Order.Status.CART)
            .prefetch_related('items__food')
        )

    @extend_schema(
        tags=[ORDERS],
        summary='Cancel an order',
        description='Only orders in the `placed` state can be cancelled.',
        request=None,
        responses={
            200: serializers.OrderSerializer,
            400: OpenApiResponse(description='The order is no longer in the "placed" state.'),
        },
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order that has been placed but not yet prepared."""
        order = self.get_object()
        if order.status != Order.Status.PLACED:
            raise ValidationError({'detail': 'Only orders in the "placed" state can be cancelled.'})
        order.status = Order.Status.CANCELLED
        order.save(update_fields=['status'])
        return Response(self.get_serializer(order).data)
