import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.form = PostForm()
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_title_label(self):
        """Проверка переопределенных лейблов"""
        expected_labels = {
            'text': 'Текст',
            'group': 'Группа',
        }
        for label_name, label in expected_labels.items():
            with self.subTest(lebel_name=label_name):
                title_label = PostFormTests.form.fields[label_name].label
                self.assertTrue(title_label, label)

    def test_title_help_text(self):
        """Проверка переопределенного вспомогательного текста"""
        expected_help_texts = {
            'text': ('Это текст вашего поста'),
            'group': ('Укажите группу, к которой будет относится ваш пост'),
        }
        for label_name, text in expected_help_texts.items():
            with self.subTest(label_name=label_name):
                title_help_text = PostFormTests.form.fields[label_name]
                self.assertTrue(title_help_text, text)

    def test_create_post(self):
        """
        Проверка создания поста: пост должен создаться
        при отправке валидной формы, перенаправление на профайл пользователя
        """
        post_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.user.username}
        ))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), post_count + 1)
        # Проверка наличия поста
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group']
            ).exists()
        )
        # Проверка полей поста
        created_post = Post.objects.filter(
            text=form_data['text'],
            group=form_data['group']
        ).first()
        for field_name, value in form_data.items():
            with self.subTest(field_name=field_name):
                self.assertTrue(getattr(created_post, field_name), value)

        self.assertTrue(
            getattr(created_post, 'author'), PostFormTests.user.username
        )

    def test_guest_create_post(self):
        """
        Проверка создания поста неавторизованным пользователем.
        Должно произойти перенаправление на авторизацию
        """
        post_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTests.group.id
        }

        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_create'),
        )
        # Проверяем, что число постов не увеличилось
        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_post(self):
        """
        Проверка редактирования поста автором.
        Пост должен быть отредактирован,
        произойти перенаправление на страницу поста
        """
        post_id = Post.objects.first().id
        form_data = {
            'text': 'Тестовый текст 1',
            'group': PostFormTests.group.id
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group']
            ).exists()
        )

    def test_guest_edit_post(self):
        """
        Проверка редактирования поста гостем.
        Пост не должен быть отредактирован,
        должно произойти перенаправление на страницу поста
        """
        post_orig = Post.objects.first()
        post_id = post_orig.id
        form_data = {
            'text': 'Тестовый текст 2',
            'group': PostFormTests.group.id
        }

        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        post_after = get_object_or_404(Post, pk=post_id)
        self.assertEqual(post_after.text, post_orig.text)

    def test_add_comment_guest(self):
        post_for_comment = Post.objects.first()
        post_id = post_for_comment.id

        comments_count = post_for_comment.comments.count()

        form_data = {
            'text': "Текст комментария",
        }

        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('users:login') + '?next='
            + reverse('posts:add_comment', kwargs={'post_id': post_id})
        )
        self.assertEqual(post_for_comment.comments.count(), comments_count)

    def test_add_comment_authorized(self):
        post_for_comment = Post.objects.first()
        post_id = post_for_comment.id

        comments_count = post_for_comment.comments.count()

        form_data = {
            'text': "Текст комментария",
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )

        self.assertEqual(post_for_comment.comments.count(), comments_count + 1)
