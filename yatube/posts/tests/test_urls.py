# posts/tests/tests_url.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
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

    def tearDown(self):
        cache.clear()

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем клиент-автор
        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.user)

        self.public_link_list = [
            '/',
            f'/group/{PostsURLTests.group.slug}/',
            '/profile/auth/',
            f'/posts/{PostsURLTests.post.pk}/',
        ]

    def test_unauthorized_accesible(self):
        """
        Проверка доступа к общедоступным страницам
        неавторизованным пользователем.
        """
        for address in self.public_link_list:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_accesible(self):
        """
        Проверка доступа к страницам авторизованным пользователем.
        """
        link_list = self.public_link_list
        link_list.append('/create/')
        for address in link_list:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_accesible(self):
        """Проверка доступа к страницам авторизованным пользователем."""
        link_list = self.public_link_list
        link_list.append('/create/')
        link_list.append(f'/posts/{PostsURLTests.post.pk}/edit/')
        for address in link_list:
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_anonymous_to_login_on_create(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_create'),
        )

    def test_guest_redirect_on_edit(self):
        """Страница по адресу /posts/{post_id}/edit/ перенаправит гостя
        на страницу поста.
        """
        response = self.guest_client.get(
            f'/posts/{PostsURLTests.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsURLTests.post.pk}
            ),
        )

    def test_authorized_redirect_on_edit(self):
        """Страница по адресу /posts/{post_id}/edit/ перенаправит не автора
        на страницу поста.
        """
        response = self.authorized_client.get(
            f'/posts/{PostsURLTests.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsURLTests.post.pk}
            ),
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        post_id = PostsURLTests.post.pk
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostsURLTests.group.slug}/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{post_id}/': 'posts/post_detail.html',
            f'/posts/{post_id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
