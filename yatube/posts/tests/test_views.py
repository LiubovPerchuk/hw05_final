import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        image = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="test_image.jpg",
            content=image,
            content_type="image/jpg"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            pub_date="Тестовая дата",
            group=cls.group,
            image=uploaded,
        )
        cls.group_without_posts = Group.objects.create(
            title="Вторая тестовая группа",
            slug="test-slug_1",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:index"))
        first_object = response.context["page_obj"][0]
        context_obj = {
            self.user: first_object.author,
            self.post.text: first_object.text,
            self.group: first_object.group,
            self.post.id: first_object.id,
        }
        for reverse_name, response_name in context_obj.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_group_list_show_correct_context(self):
        """Шаблон "group_list" сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug}))
        for post in response.context["page_obj"]:
            self.assertEqual(post.group, self.group)

    def test_profile_show_correct_context(self):
        """Шаблон "profile" сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username}))
        for post in response.context["page_obj"]:
            self.assertEqual(post.author, self.user)

    def test_post_detail_show_correct_context(self):
        """Шаблон "post_detail" сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}))
        post_id = response.context["post"].id
        self.assertEqual(post_id, self.post.id)

    def test_pages_contains_new_post_and_added_correctly(self):
        """При создании поста с группой он появляется на главной странице,
        странице с выбранной группой, в профайле пользователя."""
        adresses = [
            reverse("posts:index"),
            reverse("posts:group_list",
                    kwargs={"slug": self.group.slug}),
            reverse("posts:profile", kwargs={"username": self.post.author})
        ]
        for reverse_name in adresses:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(self.post, response.context["page_obj"])

    def test_post_in_the_right_group(self):
        """Проверяем, что пост не попал в другую группу."""
        response = self.authorized_client.get(
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group_without_posts.slug})
        )
        self.assertEqual(len(response.context["page_obj"]), 0)

    def test_post_with_image_added_in_context(self):
        """Проверяем, что при выводе поста с картинкой
        изображение передаётся в словаре context."""
        addresses = {
            reverse("posts:index"): self.post.image,
            reverse("posts:profile",
                    kwargs={"username": self.user.username}): self.post.image,
            reverse("posts:group_list",
                    kwargs={"slug": self.group.slug}): self.post.image,
        }
        for value, expected in addresses.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context["page_obj"][0]
                self.assertEqual(first_object.image, expected)

    def test_post_with_image_added_in_context_post_detail(self):
        """Проверяем, что при выводе поста с картинкой изображение
        передаётся в словаре context на отдельную страницу поста ."""
        response = self.authorized_client.get(
            reverse("posts:post_detail",
                    kwargs={"post_id": self.post.id}))
        post = response.context["post"]
        self.assertEqual(post.image, self.post.image)

    def test_postform_create_with_image_added_form_in_database(self):
        """Проверяем, что при отправке поста с картинкой
        через форму PostForm создаётся запись в базе данных."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)


class CaheTests(TestCase):
    """Проверка функции кэширования."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="test-user")
        cls.post_cash = Post.objects.create(
            author=cls.user,
            text="Тестируем cashe",
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Проверка работы cache на главной страницы"""
        response = self.authorized_client.get(
            reverse("posts:index")).content
        self.post_cash.delete()
        response_cache = self.authorized_client.get(
            reverse("posts:index")).content
        self.assertEqual(response, response_cache)
        cache.clear()
        response_clear = self.authorized_client.get(
            reverse("posts:index")).content
        self.assertNotEqual(response, response_clear)


class PostPaginatorTest(TestCase):
    """Проверка функции паджинации."""
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

        Post.objects.bulk_create(
            [Post(text=f"Тестовый текст{i}", author=cls.user, group=cls.group)
                for i in range(1, 13)]
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Шаблоны "index, group_list и profile" содержат первые 10 постов."""
        count_posts = 10
        pages = {
            "posts:index": reverse("posts:index"),
            "posts:group_list": reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}),
            "posts:profile": reverse(
                "posts:profile", kwargs={"username": self.user.username}),
        }
        for template, reverse_name in pages.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context["page_obj"]), count_posts)

    def test_second_page_contains_three_records(self):
        """Шаблоны "index, group_list и profile" содержат 3 поста."""
        count_posts = 3
        pages = {
            "posts:index": reverse("posts:index") + "?page=2",
            "posts:group_list": reverse(
                "posts:group_list",
                kwargs={"slug": self.group.slug}) + "?page=2",
            "posts:profile": reverse(
                "posts:profile",
                kwargs={"username": self.user.username}) + "?page=2",
        }
        for template, reverse_name in pages.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context["page_obj"]), count_posts)


class FollowViewTest(TestCase):
    """Проверка функции подписки."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="user")
        cls.author = User.objects.create_user(username="author")

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_autorized_user_can_follow(self):
        """Авторизованный пользователь может подписаться."""
        follow_count = Follow.objects.count()
        response = (self.authorized_client.get(
            reverse("posts:profile_follow",
                    kwargs={"username": self.author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.author
        ).exists())

    def test_autorized_user_can_unfollow(self):
        """Авторизованный пользователь может отписаться."""
        author = self.user
        Follow.objects.create(user=self.user, author=author)
        follow_count = Follow.objects.count()
        response = (self.authorized_client.
                    get(reverse("posts:profile_unfollow",
                        kwargs={"username": author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=author
        ).exists())

    def test_new_post_appear_on_follower_page(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        self.post = Post.objects.create(
            text="Тестовый текст", author=self.author
        )
        Follow.objects.create(author=self.author, user=self.user)
        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(response.context["page_obj"][0], self.post)

    def test_new_post_does_not_appear_on_follower_page(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""
        self.post = Post.objects.create(
            text="Тестовый текст", author=self.author
        )
        Follow.objects.create(author=self.author, user=self.user)
        self.second_user = User.objects.create_user(
            username="username",
        )
        self.authorized_client.force_login(self.second_user)
        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 0)
