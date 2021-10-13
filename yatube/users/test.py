from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.test import Client, TestCase
from django.urls import reverse

from .forms import CreationForm

User = get_user_model()


class CreationFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CreationForm()

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.link_list = [
            '/auth/signup/',
            '/auth/logout/',
            '/auth/login/',
        ]

    def test_urls(self):
        """Проверка доступа к страницам"""
        for address in self.link_list:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_templates(self):
        """Проверка использования корректных шаблонов"""
        templates_pages_names = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:login'): 'users/login.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_user(self):
        """
        Проверка успешного создания пользователя
        Должен произойти редирект на главную страницу
        Здесь же проверка контекста
        """
        response = self.guest_client.get(reverse('users:login'))
        self.assertIsInstance(response.context['form'], AuthenticationForm)

        user_count = User.objects.count()

        form_data = {
            'first_name': 'First',
            'last_name': 'Last',
            'username': 'usrnm1',
            'email': 'eml1@eml1.inl',
            'password1': 'p@$sworD',
            'password2': 'p@$sworD',
        }

        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:index'))
        # Проверяем, увеличилось ли число пользователей
        self.assertEqual(User.objects.count(), user_count + 1)
        # Проверяем, что создалась запись с заданными параметрами
        self.assertTrue(
            User.objects.filter(
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
                username=form_data['username'],
                email=form_data['email'],
            ).exists()
        )
