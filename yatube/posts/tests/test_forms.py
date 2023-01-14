import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.auth,
            text="Тестовый пост",
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.auth)

        self.guest_client = Client()

    def test_unauth_user_cant_publish_comment(self):
        form_data = {
            "post": self.post,
            "author": self.guest_client,
            "text": "Тестовый комментарий"
        }
        response = self.guest_client.post(
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_user_can_publish_comment(self):
        form_data = {
            "post": self.post,
            "author": self.auth,
            "text": "Тестовый комментарий"
        }
        response = self.authorized_author.post(
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        comment_attributes = {
            comment.post: self.post,
            comment.author: self.auth,
            comment.text: form_data["text"]
        }
        for attribute, value in comment_attributes.items():
            with self.subTest(attribute=attribute):
                self.assertEqual(attribute, value)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unauth_user_cant_publish_post(self):
        """При попытке создания поста гостем получаем редирект,
        число постов не поменялось"""
        form_data = {
            "text": "Текст из формы",
            "group": self.group.id,
        }
        response = self.guest_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 1)
        self.assertRedirects(response, "/auth/login/?next=/create/")

    def test_edit_post(self):
        """При отправке валидной формы со страницы редактирования поста
        reverse('posts:post_edit', args=('post_id',))
        происходит изменение поста с post_id в базе данных.
        """
        new_small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        new_uploaded = SimpleUploadedFile(
            name='new_small.gif',
            content=new_small_gif,
            content_type='image/gif'
        )
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        form_data = {
            "text": "Текст из формы редактирования",
            "group": new_group.id,
            "image": new_uploaded,
        }
        response = self.authorized_author.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        post_attributes = {
            post.author: self.auth,
            post.text: form_data["text"],
            post.group: new_group,
            post.image: f"posts/{form_data['image'].name}"
        }
        for attribute, value in post_attributes.items():
            with self.subTest(attribute=attribute):
                self.assertEqual(attribute, value)
        self.assertRedirects(response, reverse(
            "posts:post_detail", kwargs={"post_id": post.pk}))

    def test_create_post(self):
        """При отправке валидной формы со страницы создания поста
        reverse('posts:create_post')
        создаётся новая запись в базе данных.
        """
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
            "text": "Текст из формы",
            "group": self.group.id,
            "image": uploaded,
        }
        response = self.authorized_author.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 2)
        post = Post.objects.first()
        post_attributes = {
            post.author: self.auth,
            post.text: form_data["text"],
            post.group: self.group,
            post.image: f"posts/{form_data['image'].name}"
        }
        for attribute, value in post_attributes.items():
            with self.subTest(attribute=attribute):
                self.assertEqual(attribute, value)

        self.assertRedirects(response, reverse(
            "posts:profile", kwargs={"username": self.auth}))
