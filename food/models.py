from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

MAX_QUANTITY = 50


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, allow_unicode=True)
    img = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Food(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    desc = models.TextField()
    price = models.PositiveIntegerField()
    # PROTECT: deleting a category must not silently delete its whole menu.
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='foods')
    img = models.ImageField(upload_to='foods/', blank=True, null=True)
    available = models.BooleanField(default=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True, allow_unicode=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True)[:70] or 'food'
            slug, n = base, 2
            while Food.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # New comments stay hidden until an admin approves them.
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} on {self.food}'


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['user', 'food'], name='unique_favorite_per_user'),
        ]

    def __str__(self):
        return f'{self.user} likes {self.food}'


class Order(models.Model):
    """A user's cart (status=cart) or an order they have placed.

    A user has at most one cart at a time; checkout turns the cart into an order.
    """

    class Status(models.TextChoices):
        CART = 'cart', 'Cart'
        PLACED = 'placed', 'Placed'
        PREPARING = 'preparing', 'Preparing'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CART, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    placed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(status='cart'),
                name='unique_cart_per_user',
            ),
        ]

    def __str__(self):
        return f'Order #{self.pk} ({self.status})'

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    # PROTECT: ordered foods must stay in the DB so order history remains valid.
    food = models.ForeignKey(Food, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(MAX_QUANTITY)],
    )
    # Price snapshot: later menu price changes do not rewrite placed orders.
    unit_price = models.PositiveIntegerField()

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['order', 'food'], name='unique_food_per_order'),
        ]

    def __str__(self):
        return f'{self.quantity} x {self.food}'

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
