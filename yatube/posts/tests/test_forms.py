import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings

from ..models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user)
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
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
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый заголовок',
            'group': self.group.id,
            'image': uploaded}
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small.gif'
            ).exists())

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Редактированый пост',
            'group': self.group.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                text=form_data['text'],
                group=form_data['group'],
                author=self.user
            ).exists())

    def test_guest_create_post(self):
        """Неавторизованный пользователь, отправляя валидную форму,
        c /create/ не может сохранить пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый заголовок',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse(
            'posts:post_create'))
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                author=self.user
            ).exists())

    def test_guest_edit_post(self):
        """Неавторизованный пользователь, отправляя валидную форму,
        c /edit/ не может сохранить пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый заголовок',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertFalse(
            Post.objects.filter(
                id=self.post.id,
                text=form_data['text'],
                group=form_data['group']
            ).exists())

    def test_guest_comment_post(self):
        """Неавторизованный пользователь, отправляя валидную форму,
        c /comment/ не может сохранить пост."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый заголовок',
        }
        self.guest_client.post(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            data=form_data)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(
                text=form_data['text'],
                post=self.post,
                author=self.user
            ).exists())
