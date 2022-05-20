import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from ..models import Post, Group, Comment, Follow
from ..forms import PostForm, CommentForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_img = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_img,
            content_type='image/gif')
        cls.user = User.objects.create_user(username='NoName')
        cls.user_second = User.objects.create_user(username='SecondUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы')
        cls.group_second = Group.objects.create(
            title='Вторая Тестовая группа',
            slug='second_group',
            description='Тестовое описание для второй группы')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            image=uploaded,
            group=cls.group)
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @ classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_group_profile_show_correct_context(self):
        """Шаблон index, group_list, profile сформирован
        с правильным контекстом."""
        test_page = (
            (reverse('posts:index'), 'page_obj'),
            (reverse('posts:group_list',
                     kwargs={'slug': self.group.slug}), 'page_obj'),
            (reverse('posts:profile',
                     kwargs={'username': self.user.username}), 'page_obj'))
        for (page, context) in test_page:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                object_context = response.context[context]
                self.assertIn(self.post, object_context.object_list)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        context_object = response.context['post']
        form_comment_object = response.context['form']
        comment_object = response.context['comments']
        self.assertEqual(self.post, context_object)
        self.assertIsInstance(form_comment_object, CommentForm)
        self.assertIn(self.comment, comment_object)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_field = response.context.get('form')
        self.assertIsInstance(form_field, PostForm)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_field = response.context.get('form')
        self.assertIsInstance(form_field, PostForm)
        self.assertEqual(form_field.instance, self.post)

    def test_create_post_add_on_pages(self):
        """Созданый пост не попадает в другую группу"""
        response_test = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group_second.slug}))
        self.assertNotIn(self.post, response_test.context['page_obj'])

    def test_following(self):
        """Авторизованный пользователь может подписываться на других пользователей
        и удалять их из подписок"""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_second.username}))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user_second
            ).exists())
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_second.username}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user_second
            ).exists())

    def test_follow_index(self):
        """Новая запись появляется в ленте тех, кто на него подписан
        и не появляется в тенте тех кто не подписан"""
        new_post = Post.objects.create(
            text='Тестовый пост2',
            author=self.user_second,
            group=self.group)
        user_test = User.objects.create_user(username='testUser')
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_second.username}))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        context = response.context['page_obj']
        self.assertIn(new_post, context.object_list)
        self.authorized_client.force_login(user_test)
        response_second = self.authorized_client.get(
            reverse('posts:follow_index'))
        context_second = response_second.context['page_obj']
        self.assertNotIn(new_post, context_second.object_list)
