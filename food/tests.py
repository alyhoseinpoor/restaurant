from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Food, Category, Order, Comment, Favorite

User = get_user_model()


def result_count(response):
    data = response.data
    if isinstance(data, dict) and 'results' in data:
        return len(data['results'])
    return len(data)


class BaseSetup(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass12345')
        self.user2 = User.objects.create_user(username='user2', password='pass12345')
        self.admin = User.objects.create_user(username='admin', password='pass12345', is_staff=True)

        self.category = Category.objects.create(name='پیتزا', slug='pizza')
        self.food = Food.objects.create(
            title='پیتزا پپرونی', desc='توضیح', price=200000,
            category=self.category, slug='pizza-pepperoni',
        )


class AuthTests(BaseSetup):
    def test_login_returns_tokens(self):
        res = self.client.post('/api/token/', {'username': 'user1', 'password': 'pass12345'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_login_wrong_password_fails(self):
        res = self.client.post('/api/token/', {'username': 'user1', 'password': 'wrong'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class FoodPermissionTests(BaseSetup):
    def test_anyone_can_list_foods(self):
        res = self.client.get('/api/foods/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_create_food(self):
        res = self.client.post('/api/foods/', {
            'title': 'غذای جدید', 'desc': 'x', 'price': 1000,
            'category': self.category.id, 'slug': 'new-food',
        })
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_normal_user_cannot_create_food(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post('/api/foods/', {
            'title': 'غذای جدید', 'desc': 'x', 'price': 1000,
            'category': self.category.id, 'slug': 'new-food-2',
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_food(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post('/api/foods/', {
            'title': 'غذای جدید', 'desc': 'x', 'price': 1000,
            'category': self.category.id, 'slug': 'new-food-3',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_category_filter_works(self):
        other_cat = Category.objects.create(name='ساندویچ', slug='sandwich')
        Food.objects.create(title='ساندویچ مرغ', desc='x', price=1000, category=other_cat, slug='chicken-sandwich')

        res = self.client.get('/api/foods/?category=sandwich')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data['results'] if isinstance(res.data, dict) else res.data
        titles = [f['title'] for f in results]
        self.assertIn('ساندویچ مرغ', titles)
        self.assertNotIn('پیتزا پپرونی', titles)


class OrderTests(BaseSetup):
    def test_anonymous_cannot_create_order(self):
        res = self.client.post('/api/orders/', {'food': self.food.id, 'number': 1})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_order(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post('/api/orders/', {'food': self.food.id, 'number': 1})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(id=res.data['id'])
        self.assertEqual(order.user, self.user1)  # مطمئن می‌شیم user از request اومده نه از payload

    def test_user_cannot_see_other_users_orders(self):
        Order.objects.create(user=self.user1, food=self.food, number=1)

        self.client.force_authenticate(user=self.user2)
        res = self.client.get('/api/orders/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(result_count(res), 0)

    def test_increase_and_decrease_actions(self):
        order = Order.objects.create(user=self.user1, food=self.food, number=1)
        self.client.force_authenticate(user=self.user1)

        res = self.client.post(f'/api/orders/{order.id}/increase/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.number, 2)

        self.client.post(f'/api/orders/{order.id}/decrease/')
        order.refresh_from_db()
        self.assertEqual(order.number, 1)

    def test_finalize_marks_order_active(self):
        order = Order.objects.create(user=self.user1, food=self.food, number=1)
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(f'/api/orders/{order.id}/finalize/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertTrue(order.active)


class CommentTests(BaseSetup):
    def test_anonymous_cannot_create_comment(self):
        res = self.client.post('/api/comments/', {'food': self.food.id, 'text': 'خوب بود'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_comment_is_inactive_by_default_and_hidden_from_list(self):
        self.client.force_authenticate(user=self.user1)
        create_res = self.client.post('/api/comments/', {'food': self.food.id, 'text': 'خوب بود'})
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        comment = Comment.objects.get(id=create_res.data['id'])
        self.assertFalse(comment.active)  # هنوز تأیید نشده

        list_res = self.client.get('/api/comments/')
        self.assertEqual(result_count(list_res), 0)  # پس توی لیست عمومی نباید باشه

    def test_approved_comment_appears_in_list(self):
        Comment.objects.create(user=self.user1, food=self.food, text='عالی بود', active=True)
        self.client.force_authenticate(user=self.user2)
        res = self.client.get('/api/comments/')
        self.assertEqual(result_count(res), 1)


class FavoriteTests(BaseSetup):
    def test_anonymous_cannot_add_favorite(self):
        res = self.client.post('/api/favorites/', {'food': self.food.id})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_add_favorite(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post('/api/favorites/', {'food': self.food.id})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_user_only_sees_own_favorites(self):
        Favorite.objects.create(user=self.user1, food=self.food)
        self.client.force_authenticate(user=self.user2)
        res = self.client.get('/api/favorites/')
        self.assertEqual(result_count(res), 0)