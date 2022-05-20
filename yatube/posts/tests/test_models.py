from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост.Тестовый пост.',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        field_str_class = (
            (self.post, self.post.text[:15]),
            (self.group, self.group.title))
        for field, value in field_str_class:
            with self.subTest(field=field):
                self.assertEqual(str(field), value)

    def test_verbose_name_on_post(self):
        """Проверяем корректность работы verbose_name для post"""
        field_verboses = (
            ('text', 'Текст'),
            ('author', 'Автор'),
            ('group', 'Группа'))
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value)

    def test_help_text_on_post(self):
        """Проверяем корректность работы help_text для post"""
        field_help_text = (
            ('text', 'Введите текст записи'),
            ('author', ''),
            ('group', 'Выберите группу для публикации'))
        for field, expected_value in field_help_text:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value)
