from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            pub_date="Тестовая дата",
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "/": "posts/index.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/profile/{self.user.username}/": "posts/profile.html",
            f"/posts/{self.post.id}/": "posts/post_detail.html",
            "/create/": "posts/create_or_update_post.html",
            f"/posts/{self.post.id}/edit/": "posts/create_or_update_post.html",
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexist_url_return_404_error(self):
        """Запрос к несуществующей странице вернет ошибку 404"""
        response = self.authorized_client.get("/posts/unexisting/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_accsess_urls_for_guest_client(self):
        """Доступ неавторизованному пользователю"""
        pages = {
            "/",
            f"/group/{self.group.slug}/",
            f"/profile/{self.user.username}/",
            f"/posts/{self.post.id}/"
        }
        for page in pages:
            response = self.guest_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_accsess_post_create_for_authorized_client(self):
        """Доступ авторизованному пользователю на страницу /create/."""
        response = self.authorized_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_accsess_post_edit_for_guest_client(self):
        """Доступ неавторизованному пользователю
        на страницу редактирования поста /post_edit/."""
        post_id = self.post.id
        response = self.guest_client.get(
            reverse("posts:post_edit", kwargs={"post_id": post_id})
        )
        self.assertRedirects(
            response, f"/auth/login/?next=/posts/{self.post.id}/edit/")
