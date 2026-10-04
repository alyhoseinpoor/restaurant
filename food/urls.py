from django.urls import path, include
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    FoodViewSet,
    CategoryViewSet,
    OrderViewSet,
    CommentListCreate,
    FavoriteListCreate
)

router = DefaultRouter()
router.register('foods', FoodViewSet)
router.register('categories', CategoryViewSet)
router.register('orders', OrderViewSet)


urlpatterns = [
    path('api/', include(router.urls)),

    # APIView 
    path('api/comments/', CommentListCreate.as_view()),
    path('api/favorites/', FavoriteListCreate.as_view()),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]