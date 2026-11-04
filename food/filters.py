from django_filters import rest_framework as filters

from .models import Food


class FoodFilter(filters.FilterSet):
    category = filters.CharFilter(field_name='category__slug')
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Food
        fields = ['category', 'available', 'min_price', 'max_price']
