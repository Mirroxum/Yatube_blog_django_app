from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Проверка кэша страницы индекс."""
        response_first = self.authorized_client.get(
            reverse('posts:index')).content
        self.post.delete()
        response_second = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(response_first, response_second)
        cache.clear()
        response_third = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(response_third, response_second)
