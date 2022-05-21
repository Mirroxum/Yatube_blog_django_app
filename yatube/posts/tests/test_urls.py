from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author_user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий name."""
        self.authorized_client.force_login(self.author_user)
        templates_pages_names = (
            (reverse('posts:index'), '/'),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             f'/group/{self.group.slug}/'),
            (reverse('posts:profile',
                     kwargs={'username': self.user.username}),
             f'/profile/{self.user.username}/'),
            (reverse('posts:post_detail',
                     kwargs={'post_id': self.post.id}),
             f'/posts/{self.post.id}/'),
            (reverse('posts:post_edit',
                     kwargs={'post_id': self.post.id}),
             f'/posts/{self.post.id}/edit/'),
            (reverse('posts:post_create'), '/create/'),
            (reverse('posts:follow_index'), '/follow/'))
        for reverse_name, url in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(reverse_name, url)

    def test_urls_uses_correct_template(self):
        """Проверка запросов и ответа шаблона для автора поста"""
        self.authorized_client.force_login(self.author_user)
        templates_url_names = (
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             'posts/group_list.html'),
            (reverse('posts:profile', kwargs={'username': self.user.username}),
             'posts/profile.html'),
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
             'posts/post_detail.html'),
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
             'posts/form_post.html'),
            (reverse('posts:post_create'), 'posts/form_post.html'),
            (reverse('posts:follow_index'), 'posts/follow.html'))
        for address, template in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_redirect_create_on_guest(self):
        """Проверка редиректа для гостя со страниц /create/ и /posts/1/edit/"""
        url_redirect = {
            reverse('posts:post_create'): reverse('users:login')
            + '?next=' + reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}):
            reverse('users:login') + '?next=' + reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id})}
        for reverse_name, redirect in url_redirect.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name, follow=True)
                self.assertRedirects(response, redirect)

    def test_urls_uses_correct_redirect_edit_on_user(self):
        """Страница по адресу /posts/1/edit/ перенаправит
        не автора на страницу поста."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}), follow=True)
        redirect = reverse('posts:post_detail',
                           kwargs={'post_id': self.post.id})
        self.assertRedirects(response, redirect)

    def test_urls_for_guest_user_author(self):
        """Проверка доступности страниц для всех типов пользователя"""
        test_urls = (
            (reverse('posts:index'), HTTPStatus.OK, False),
            (reverse('posts:group_list',
                     kwargs={'slug': self.group.slug}),
             HTTPStatus.OK, False),
            (reverse('posts:profile',
                     kwargs={'username': self.user.username}),
             HTTPStatus.OK, False),
            (reverse('posts:post_detail',
                     kwargs={'post_id': self.post.id}),
             HTTPStatus.OK, False),
            (reverse('posts:post_edit',
                     kwargs={'post_id': self.post.id}),
             HTTPStatus.OK, True),
            (reverse('posts:post_edit',
                     kwargs={'post_id': self.post.id}),
             HTTPStatus.FOUND, False),
            (reverse('posts:post_create'), HTTPStatus.FOUND, False),
            (reverse('posts:post_create'), HTTPStatus.OK, True),
            (reverse('posts:follow_index'), HTTPStatus.FOUND, False),
            (reverse('posts:follow_index'), HTTPStatus.OK, True),
            ('/not_page/', HTTPStatus.NOT_FOUND, True))
        for test_url, status, auth in test_urls:
            with self.subTest(test_urls=test_urls):
                if auth:
                    self.authorized_client.force_login(self.author_user)
                    response = self.authorized_client.get(test_url)
                else:
                    response = self.guest_client.get(test_url)
                self.assertEqual(response.status_code, status)
