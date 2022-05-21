from math import ceil
from time import sleep

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..models import Follow, Post, Group

User = get_user_model()
COUNT_POST_WITH_GROUP = 13
COUNT_POST_WITHOUT_GROUP = 17
COUNT_POST_WITH_SECOND_GROUP_AND_SECOND_USER = 10


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_second = User.objects.create_user(username='NoName_Second')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы')
        cls.group_second = Group.objects.create(
            title='Вторая тестовая группа',
            slug='test_group_second',
            description='Lorem Ipsum')
        cls.post = []
        for count_post in range(COUNT_POST_WITH_GROUP):
            sleep(0.001)
            cls.post.append(
                Post.objects.create(
                    text=f'Тестовый пост №{count_post}, без указания группы',
                    author=cls.user,
                    group=cls.group))
        for count_post in range(COUNT_POST_WITHOUT_GROUP):
            sleep(0.001)
            cls.post.append(
                Post.objects.create(
                    text=f'Тестовый пост №{count_post}, с указанием группы',
                    author=cls.user))
        for count_post in range(COUNT_POST_WITH_SECOND_GROUP_AND_SECOND_USER):
            sleep(0.001)
            cls.post.append(
                Post.objects.create(
                    text=f'Тестовый пост №{count_post}, с другими',
                    author=cls.user_second,
                    group=cls.group_second))
        Follow.objects.create(
            user=cls.user,
            author=cls.user_second)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_profile_group_first_page_count_paginator(self):
        """Проверка количества постов на первой странице
        index, group, profile, index_follow при превышении
        максимального количества постов на страницу"""
        test_page = (
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username': self.user_second.username}),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:follow_index'))
        for page in test_page:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.MAX_PAGE_AMOUNT)

    def test_index_profile_group_last_page_count_paginator(self):
        """Проверка количества постов на последних
        страницах index, group, profile"""
        count_index_page = ceil(
            len(self.post) / settings.MAX_PAGE_AMOUNT)
        count_profile_page = ceil(
            (COUNT_POST_WITHOUT_GROUP + COUNT_POST_WITH_GROUP)
            / settings.MAX_PAGE_AMOUNT)
        count_group_page = ceil(
            COUNT_POST_WITH_GROUP / settings.MAX_PAGE_AMOUNT)
        count_follow_page = ceil(
            COUNT_POST_WITH_SECOND_GROUP_AND_SECOND_USER
            / settings.MAX_PAGE_AMOUNT)
        count_post_last_index_page = (
            len(self.post) - (count_index_page - 1)
            * settings.MAX_PAGE_AMOUNT)
        count_post_last_profile_page = (
            (COUNT_POST_WITHOUT_GROUP + COUNT_POST_WITH_GROUP)
            - (count_profile_page - 1) * settings.MAX_PAGE_AMOUNT)
        count_post_last_group_page = (
            COUNT_POST_WITH_GROUP - (count_group_page - 1)
            * settings.MAX_PAGE_AMOUNT)
        count_post_last_follow_page = (
            COUNT_POST_WITH_SECOND_GROUP_AND_SECOND_USER
            - (count_follow_page - 1) * settings.MAX_PAGE_AMOUNT)
        test_last_page = (
            (reverse('posts:index')
             + f'?page={count_index_page}', count_post_last_index_page),
            (reverse('posts:profile', kwargs={
             'username': self.user.username})
             + f'?page={count_profile_page}',
             count_post_last_profile_page),
            (reverse('posts:group_list',
                     kwargs={'slug': self.group.slug})
             + f'?page={count_group_page}',
             count_post_last_group_page),
            (reverse('posts:follow_index')
             + f'?page={count_follow_page}',
             count_post_last_follow_page))
        for page, count in test_last_page:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    len(response.context['page_obj'].object_list), count)
