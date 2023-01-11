from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-task",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.auth,
            text='Тестовый пост',
            group=cls.group,
        )

    def test_models_have_correct_object_names(self):
        """__str__ у моделей работает корректно."""
        group = PostModelTest.group
        post = PostModelTest.post
        models = {
            group: group.title,
            post: post.text[:15]
        }
        for model, model_str in models.items():
            with self.subTest(model=model):
                self.assertEqual(model_str, str(model))

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            "text": "Текст нового поста",
            "group": "Группа, к которой будет относиться пост",
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            "text": "Текст поста",
            "created": "Дата создания",
            "author": "Автор",
            "group": "Группа",
            "image": "Картинка"
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)
