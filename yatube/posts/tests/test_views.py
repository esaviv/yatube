import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.auth = User.objects.create_user(username="auth")
        cls.user = User.objects.create_user(username="user")
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.auth,
            text="Тестовый пост",
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.auth)

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адреса используют правильные шаблоны."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse("posts:profile",
                    kwargs={"username": f"{self.auth}"}
                    ): "posts/profile.html",
            reverse("posts:group_list",
                    kwargs={"slug": f"{self.group.slug}"}
                    ): "posts/group_list.html",
            reverse("posts:post_detail",
                    kwargs={"post_id": f"{self.post.pk}"}
                    ): "posts/post_detail.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse("posts:post_edit",
                    kwargs={"post_id": f"{self.post.pk}"}
                    ): "posts/create_post.html",
            reverse("posts:follow_index"): "posts/follow.html"
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_post(self, post):
        post_attributes = {
            post.author: self.auth,
            post.text: self.post.text,
            post.group: self.group,
            post.image: self.post.image
        }
        for attribute, value in post_attributes.items():
            with self.subTest(attribute=attribute):
                self.assertEqual(attribute, value)

    def test_index_page_show_correct_context(self):
        """Шаблоны index сформирован
        с правильным контекстом page_obj.
        """
        response = self.authorized_author.get(
            reverse("posts:index"))
        post = response.context["page_obj"][0]
        self.check_post(post)

    def test_pages_contain_ten_records(self):
        """Шаблоны index, profile, group_list
        содержат десять записей на первой странице.
        """
        Post.objects.bulk_create([
            Post(
                text="Тестовый пост",
                author=self.auth,
                group=self.group
            ) for _ in range(1, 13)
        ])
        paginated_urls = {
            "posts:index": {},
            "posts:profile": {"username": self.auth},
            "posts:group_list": {"slug": self.group.slug}
        }
        paginator_amount = 10
        second_page_amount = 3
        pages = (
            (1, paginator_amount),
            (2, second_page_amount)
        )
        for url, kwargs in paginated_urls.items():
            for page, count in pages:
                with self.subTest(url=url, page=page):
                    response = self.authorized_author.get(
                        reverse(url, kwargs=kwargs), {'page': page})
                    self.assertEqual(len(response.context["page_obj"]), count)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse(
            "posts:group_list", kwargs={"slug": self.group.slug}))
        group = response.context["group"]
        group_attributes = {
            group.title: self.group.title,
            group.slug: self.group.slug,
            group.description: self.group.description
        }
        for attribute, value in group_attributes.items():
            with self.subTest(attribute=attribute):
                self.assertEqual(attribute, value)

        post = response.context["post"]
        self.check_post(post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile_list сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse(
            "posts:profile", kwargs={"username": self.auth}))
        author = response.context["author"]
        self.assertEqual(author, self.auth)

        post = response.context["page_obj"][0]
        self.check_post(post)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        comment = Comment.objects.create(
            post=self.post,
            author=self.auth,
            text="Тестовый комментарий"
        )
        response = self.authorized_author.get(reverse(
            "posts:post_detail", kwargs={"post_id": self.post.pk}
        ))

        form_field = response.context['form']
        self.assertIsInstance(form_field, CommentForm)

        post = response.context["post"]
        self.check_post(post)

        comment_to_post = response.context["comments"][0]
        comment_attributes = {
            comment_to_post.post: self.post,
            comment_to_post.author: self.auth,
            comment_to_post.text: comment.text
        }
        for attribute, value in comment_attributes.items():
            with self.subTest(attribute=attribute):
                self.assertEqual(attribute, value)

    def test_post_create_edit_page_show_correct_context(self):
        """Шаблоны post_create сформирован с правильным контекстом
        для создания и редоктирования поста.
        """
        urls_parameters = {
            "posts:post_create": ({}, False),
            "posts:post_edit": ({"post_id": self.post.pk}, True)
        }
        for url, parameters in urls_parameters.items():
            response = self.authorized_author.get(
                reverse(url, kwargs=parameters[0]))
            form_field = response.context['form']
            self.assertIsInstance(form_field, PostForm)

            is_edit = response.context["is_edit"]
            self.assertEqual(is_edit, parameters[1])

    def test_index_cache(self):
        """Проверка кеширования главной страницы."""
        def get_page_obj(self):
            responce = self.authorized_author.get(reverse("posts:index"))
            return responce.content

        page_obj_before_delete_posts = get_page_obj(self)

        Post.objects.all().delete()

        page_obj_after_delete_posts = get_page_obj(self)
        self.assertEqual(page_obj_before_delete_posts,
                         page_obj_after_delete_posts)

        cache.clear()

        page_obj_after_clear_cache = get_page_obj(self)
        self.assertNotEqual(page_obj_after_delete_posts,
                            page_obj_after_clear_cache)

    def test_follow_index_page_show_correct_context_follow_unfollow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.
        Запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан.
        """
        self.authorized_client.get(
            reverse("posts:profile_follow", kwargs={"username": self.auth}))

        response = self.authorized_client.get(reverse("posts:follow_index"))
        posts = response.context["page_obj"]
        self.assertEqual(len(posts), 1)
        self.check_post(posts[0])

        self.authorized_client.get(
            reverse("posts:profile_unfollow", kwargs={"username": self.auth}))

        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 0)
