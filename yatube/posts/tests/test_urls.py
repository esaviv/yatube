from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="user")
        cls.auth = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.auth,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.auth)

        self.guest_client = Client()

    def test_urls_exist_at_desired_location_anonymous(self):
        """Страницы /, /group/test-slug/, /posts/1/, /profile/auth/
        доступны любому пользователю.
        """
        urls = [
            "/",
            f"/group/{self.group.slug}/",
            f"/posts/{self.post.pk}/",
            f"/profile/{self.auth}/"
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_post_create_edit_exists_at_desired_location_authorized(self):
        """Страницы /create/, /posts/1/edit/
        доступна авторизованному автору поста"""
        urls = [
            "/create/",
            f"/posts/{self.post.pk}/edit/"
        ]
        for url in urls:
            with self.subTest(url=url):
                responce = self.authorized_author.get(url)
                self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_urls_redirect_anonymous_on_admin_login(self):
        """Страницы по адресу /create/, /posts/1/edit/,
        /follow/, /profile/auth/follow/, /profile/auth/unfollow/
        перенаправят анонимного пользователя на страницу логина.
        """
        login_first = "/auth/login/?next="
        urls = {
            "/create/": f"{login_first}/create/",
            f"/posts/{self.post.pk}/edit/":
            f"{login_first}/posts/{self.post.pk}/edit/",
            "/follow/": f"{login_first}/follow/",
            f"/profile/{self.auth}/follow/":
            f"{login_first}/profile/{self.auth}/follow/",
            f"/profile/{self.auth}/unfollow/":
            f"{login_first}/profile/{self.auth}/unfollow/"
        }
        for url, redirect_url in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response, redirect_url
                )

    def test_url_post_edit_redirect_anonymous(self):
        """Страница по адресу /posts/1/edit/ перенаправят авторизированного
        не автора на страницу с детальной информацией о посте.
        """
        authorized_client = Client()
        authorized_client.force_login(self.user)

        response = authorized_client.get(
            f"/posts/{self.post.pk}/edit/",
            follow=True)
        self.assertRedirects(response, f"/posts/{self.post.pk}/")

    def test_url_profile_follow_unfollow_redirect_to_follow_index(self):
        urls = [
            f"/profile/{self.user}/follow/",
            f"/profile/{self.user}/unfollow/"
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_author.get(
                    url,
                    follow=True)
                self.assertRedirects(response, "/follow/")

    def test_posts_urls_use_correct_template(self):
        """URL-адреса страниц, доступных аторизированному автору,
        используют соответствующие шаблоны.
        """
        url_template_names = {
            "/": "posts/index.html",
            f"/profile/{self.auth}/": "posts/profile.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/posts/{self.post.pk}/": "posts/post_detail.html",
            "/create/": "posts/create_post.html",
            f"/posts/{self.post.pk}/edit/": "posts/create_post.html",
            "/follow/": "posts/follow.html"
        }
        for url, template in url_template_names.items():
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_custom_404(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
