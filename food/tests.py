from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Comment, Favorite, Food, Order, OrderItem

User = get_user_model()
PASSWORD = 'Str0ng-Pass!word'


class BaseAPITestCase(APITestCase):
    def setUp(self):
        cache.clear()  # throttling counters live in the cache
        self.user = User.objects.create_user('ali', password=PASSWORD)
        self.other = User.objects.create_user('sara', password=PASSWORD)
        self.admin = User.objects.create_user('admin', password=PASSWORD, is_staff=True)
        self.category = Category.objects.create(name='Kebab', slug='kebab')
        self.drinks = Category.objects.create(name='Drinks', slug='drinks')
        self.food = Food.objects.create(
            title='Koobideh', desc='Grilled minced meat', price=250000, category=self.category
        )
        self.sold_out = Food.objects.create(
            title='Barg', desc='Fillet', price=300000, category=self.category, available=False
        )


class AuthTests(BaseAPITestCase):
    def test_register_then_login(self):
        resp = self.client.post(
            '/api/register/',
            {'username': 'newuser', 'email': 'n@example.com', 'password': PASSWORD},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', resp.data)

        resp = self.client.post(
            '/api/token/', {'username': 'newuser', 'password': PASSWORD}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

    def test_register_rejects_weak_password(self):
        resp = self.client.post(
            '/api/register/', {'username': 'weak', 'password': '12345678'}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cart_requires_login(self):
        resp = self.client.get('/api/cart/')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class MenuTests(BaseAPITestCase):
    def test_menu_is_public(self):
        resp = self.client.get('/api/foods/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 2)

    def test_search_by_title(self):
        resp = self.client.get('/api/foods/', {'search': 'Koob'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([f['title'] for f in resp.data['results']], ['Koobideh'])

    def test_filter_by_category_and_price(self):
        Food.objects.create(title='Doogh', desc='Drink', price=30000, category=self.drinks)
        resp = self.client.get('/api/foods/', {'category': 'drinks'})
        self.assertEqual([f['title'] for f in resp.data['results']], ['Doogh'])

        resp = self.client.get('/api/foods/', {'min_price': 280000})
        self.assertEqual([f['title'] for f in resp.data['results']], ['Barg'])

    def test_only_staff_can_modify_menu(self):
        payload = {'title': 'Soup', 'desc': 'Hot', 'price': 90000, 'category': self.category.id}

        self.client.force_authenticate(self.user)
        resp = self.client.post('/api/foods/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/foods/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['slug'], 'soup')

    def test_slug_is_generated_and_unique_for_persian_titles(self):
        first = Food.objects.create(title='کباب کوبیده', desc='x', price=1, category=self.category)
        second = Food.objects.create(title='کباب کوبیده', desc='x', price=1, category=self.category)
        self.assertEqual(first.slug, 'کباب-کوبیده')
        self.assertEqual(second.slug, 'کباب-کوبیده-2')

    def test_category_with_foods_cannot_be_deleted(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.delete(f'/api/categories/{self.category.id}/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())


class CartTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)

    def add(self, food, quantity=1):
        return self.client.post(
            '/api/cart/items/', {'food': food.id, 'quantity': quantity}, format='json'
        )

    def test_empty_cart(self):
        resp = self.client.get('/api/cart/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['items'], [])
        self.assertEqual(resp.data['total'], 0)

    def test_add_item_and_total(self):
        resp = self.add(self.food, 2)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        cart = self.client.get('/api/cart/').data
        self.assertEqual(len(cart['items']), 1)
        self.assertEqual(cart['total'], 500000)

    def test_adding_same_food_increments_quantity(self):
        self.add(self.food, 1)
        resp = self.add(self.food, 2)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['quantity'], 3)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_rejects_unavailable_food_and_bad_quantity(self):
        self.assertEqual(self.add(self.sold_out).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.add(self.food, 0).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.add(self.food, 51).status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_and_remove_item(self):
        item_id = self.add(self.food).data['id']
        resp = self.client.patch(f'/api/cart/items/{item_id}/', {'quantity': 4}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['quantity'], 4)

        resp = self.client.delete(f'/api/cart/items/{item_id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_cannot_touch_another_users_cart_item(self):
        other_cart = Order.objects.create(user=self.other)
        item = OrderItem.objects.create(
            order=other_cart, food=self.food, quantity=1, unit_price=self.food.price
        )
        resp = self.client.patch(f'/api/cart/items/{item.id}/', {'quantity': 9}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        resp = self.client.delete(f'/api/cart/items/{item.id}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_clear_cart(self):
        self.add(self.food)
        resp = self.client.delete('/api/cart/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OrderItem.objects.count(), 0)


class CheckoutAndOrderTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)

    def place_order(self):
        self.client.post('/api/cart/items/', {'food': self.food.id, 'quantity': 2}, format='json')
        return self.client.post('/api/cart/checkout/')

    def test_checkout_empty_cart_fails(self):
        resp = self.client.post('/api/cart/checkout/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_places_order_and_starts_new_cart(self):
        resp = self.place_order()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['status'], 'placed')
        self.assertEqual(resp.data['total'], 500000)
        self.assertEqual(self.client.get('/api/cart/').data['items'], [])

    def test_price_is_snapshotted_at_checkout(self):
        order_id = self.place_order().data['id']
        self.food.price = 999999
        self.food.save()
        self.assertEqual(Order.objects.get(pk=order_id).total, 500000)

    def test_checkout_fails_if_food_became_unavailable(self):
        self.client.post('/api/cart/items/', {'food': self.food.id}, format='json')
        self.food.available = False
        self.food.save()
        resp = self.client.post('/api/cart/checkout/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.get(user=self.user).status, Order.Status.CART)

    def test_orders_list_shows_only_own_placed_orders(self):
        self.place_order()
        self.client.get('/api/cart/')  # creates a fresh cart, which must not be listed
        other_order = Order.objects.create(user=self.other, status=Order.Status.PLACED)

        resp = self.client.get('/api/orders/')
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(self.client.get(f'/api/orders/{other_order.id}/').status_code, 404)

    def test_cancel_placed_order(self):
        order_id = self.place_order().data['id']
        resp = self.client.post(f'/api/orders/{order_id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'cancelled')

        resp = self.client.post(f'/api/orders/{order_id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_cancel_order_that_is_being_prepared(self):
        order_id = self.place_order().data['id']
        Order.objects.filter(pk=order_id).update(status=Order.Status.PREPARING)
        resp = self.client.post(f'/api/orders/{order_id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ordered_food_cannot_be_deleted(self):
        self.place_order()
        self.client.force_authenticate(self.admin)
        resp = self.client.delete(f'/api/foods/{self.food.id}/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class FavoriteTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)

    def test_add_list_and_remove(self):
        resp = self.client.post('/api/favorites/', {'food': self.food.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.get('/api/favorites/').data['count'], 1)

        resp = self.client.delete(f'/api/favorites/{resp.data["id"]}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_duplicate_favorite_is_a_400_not_a_500(self):
        self.client.post('/api/favorites/', {'food': self.food.id}, format='json')
        resp = self.client.post('/api/favorites/', {'food': self.food.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_see_or_delete_other_users_favorites(self):
        fav = Favorite.objects.create(user=self.other, food=self.food)
        self.assertEqual(self.client.get('/api/favorites/').data['count'], 0)
        self.assertEqual(self.client.delete(f'/api/favorites/{fav.id}/').status_code, 404)


class CommentTests(BaseAPITestCase):
    def test_comment_is_hidden_until_approved(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            '/api/comments/', {'food': self.food.id, 'text': 'Great!'}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertFalse(resp.data['active'])

        self.assertEqual(self.client.get('/api/comments/').data['count'], 0)
        Comment.objects.update(active=True)
        self.assertEqual(self.client.get('/api/comments/').data['count'], 1)

    def test_user_cannot_approve_own_comment(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            '/api/comments/',
            {'food': self.food.id, 'text': 'Spam', 'active': True},
            format='json',
        )
        self.assertFalse(resp.data['active'])

    def test_filter_comments_by_food(self):
        Comment.objects.create(user=self.user, food=self.food, text='a', active=True)
        Comment.objects.create(user=self.user, food=self.sold_out, text='b', active=True)
        resp = self.client.get('/api/comments/', {'food': self.food.id})
        self.assertEqual(resp.data['count'], 1)

    def test_anonymous_cannot_comment(self):
        resp = self.client.post(
            '/api/comments/', {'food': self.food.id, 'text': 'hi'}, format='json'
        )
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class DocsTests(BaseAPITestCase):
    def test_openapi_schema_is_served(self):
        resp = self.client.get('/api/schema/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
