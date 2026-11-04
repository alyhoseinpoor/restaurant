from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CartItemViewSet,
    CartView,
    CategoryViewSet,
    CheckoutView,
    CommentViewSet,
    FavoriteViewSet,
    FoodViewSet,
    LoginView,
    OrderViewSet,
    RegisterView,
)

router = DefaultRouter()
router.register('foods', FoodViewSet, basename='food')
router.register('categories', CategoryViewSet, basename='category')
router.register('comments', CommentViewSet, basename='comment')
router.register('favorites', FavoriteViewSet, basename='favorite')
router.register('cart/items', CartItemViewSet, basename='cart-item')
router.register('orders', OrderViewSet, basename='order')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/cart/', CartView.as_view(), name='cart'),
    path('api/cart/checkout/', CheckoutView.as_view(), name='checkout'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
