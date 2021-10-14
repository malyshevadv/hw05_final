import copy
import shutil
import tempfile
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTest.user)

        self.username = PostsViewsTest.user.username

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsViewsTest.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsViewsTest.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsViewsTest.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        # Проверяем для name вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class ContextPaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание 2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(ContextPaginatorViewsTest.user)
        self.username = ContextPaginatorViewsTest.user.username

        self.paginator_link_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': ContextPaginatorViewsTest.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.username}
            ),
        ]

        self.posts = []
        for _ in range(13):
            self.posts.append(
                Post.objects.create(
                    author=ContextPaginatorViewsTest.user,
                    text='Тестовый текст',
                    group=ContextPaginatorViewsTest.group,
                    image=ContextPaginatorViewsTest.uploaded,
                )
            )

    def tearDown(self):
        cache.clear()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_first_page_contains_ten_records(self):
        """Проверка что первая страница содержит 10 записей"""
        for reverse_name in self.paginator_link_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                # Проверка: количество постов на первой странице равно 10.
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверка что вторая страница содержит 3 записи"""
        for reverse_name in self.paginator_link_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_post_list_page_show_correct_context(self):
        """Проверка контекста страниц со списками."""
        first_post = self.posts[0]
        for reverse_name in self.paginator_link_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author.username
                post_text_0 = first_object.text
                post_group_0 = first_object.group.title
                post_date_0 = first_object.pub_date
                post_image_0 = first_object.image
                self.assertEqual(post_author_0, self.username)
                self.assertEqual(post_text_0, first_post.text)
                self.assertEqual(post_group_0, first_post.group.title)
                self.assertIsInstance(post_date_0, datetime)
                self.assertIsNotNone(post_image_0)

    def test_post_detail_page_show_correct_context(self):
        """Проверка контекста страницы с одним постом."""
        first_post = self.posts[0]
        post_id = first_post.pk
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_id})
        )
        post = response.context.get('post')
        self.assertEqual(post.author.username, self.username)
        self.assertEqual(post.text, first_post.text)
        self.assertEqual(post.group.title, first_post.group.title)
        self.assertIsInstance(post.pub_date, datetime)
        self.assertIsNotNone(post.image)

    def test_post_form_correct_context(self):
        """Проверка корректности ожидаемого контекста форм"""
        post_id = self.posts[0].pk
        pages_to_test = [
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_id}
            ),
            reverse('posts:post_create'),
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField,
        }

        for reverse_name in pages_to_test:
            for value, expected in form_fields.items():
                with self.subTest(reverse_name=reverse_name, value=value):
                    response = self.authorized_client.get(reverse_name)
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_new_post_with_group_added(self):
        """
        Проверка, что если при создании поста указать группу,
        то этот пост появляется:
            на главной странице сайта,
            на странице выбранной группы,
            в профайле пользователя.
        И не попадает в группу, для которой не был предназначен
        """
        links_to_test_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': ContextPaginatorViewsTest.group2.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.username}
            ),
        ]

        new_post = Post.objects.create(
            author=ContextPaginatorViewsTest.user,
            text='Тестовый текст',
            group=ContextPaginatorViewsTest.group2,
        )
        for reverse_name in links_to_test_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(new_post, response.context['page_obj'])

        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': ContextPaginatorViewsTest.group.slug}
            )
        )
        self.assertNotIn(new_post, response.context['page_obj'])

    def test_cache_on_delete(self):
        self.authorized_client.get(reverse('posts:index'))
        post_to_delete = Post.objects.first()
        post_to_find = copy.deepcopy(post_to_delete)

        post_to_delete.delete()
        response_1 = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response_1, post_to_find.text)

    def test_subscription(self):
        new_user = User.objects.create_user(username='IAmNew')
        new_client = Client()
        new_client.force_login(new_user)

        new_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.username}
        ))
        self.assertIn(ContextPaginatorViewsTest.user.id,
                      new_user.follower.values_list('author', flat=True))

    def test_unscription(self):
        new_user = User.objects.create_user(username='IAmNew')
        new_client = Client()
        new_client.force_login(new_user)

        Follow.objects.create(
            author=ContextPaginatorViewsTest.user, user=new_user
        )

        new_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.username}
        ))
        self.assertNotIn(ContextPaginatorViewsTest.user.id,
                         new_user.follower.values_list('author', flat=True))

    def test_check_for_post(self):
        new_user = User.objects.create_user(username='IAmNew')
        new_client = Client()
        new_client.force_login(new_user)

        Follow.objects.create(
            author=ContextPaginatorViewsTest.user, user=new_user
        )

        post_to_check = self.posts[0]

        response = new_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(post_to_check, response.context['page_obj'])

    def test_check_for_post(self):
        new_user = User.objects.create_user(username='IAmNew')
        new_client = Client()
        new_client.force_login(new_user)

        Follow.objects.create(
            author=ContextPaginatorViewsTest.user, user=new_user
        )

        post_to_check = self.posts[0]

        new_user2 = User.objects.create_user(username='IAmNewer')
        new_client2 = Client()
        new_client2.force_login(new_user2)

        response = new_client2.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(post_to_check, response.context['page_obj'])
