import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="test_author")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_form_post(self):
        """Валидная форма создает новый пост с картинкой."""
        post_count = Post.objects.count()
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
        form_data = {
            "text": "Текст нового поста",
            "group": self.group.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        new_post = Post.objects.first()
        self.assertRedirects(response, reverse(
            "posts:profile", kwargs={"username": self.author}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(new_post.text, form_data["text"])
        self.assertEqual(new_post.group.id, self.group.id)
        self.assertTrue(new_post.image.name.endswith(
            form_data["image"].name)
        )

    def test_edit_form_post_and_group(self):
        """Валидная форма изменяет текст поста и группу"""
        self.post = Post.objects.create(
            author=self.author,
            text="Тестовый пост",
            pub_date="Тестовая дата",
            group=self.group,
        )
        self.group_2 = Group.objects.create(
            title="Тестовая группа_2",
            slug="test-slug_2",
            description="Тестовое описание_2",
        )
        post_count = Post.objects.count()
        form_data = {
            "text": "Измененный текст поста",
            "group": self.group_2.id
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=False
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, reverse(
            "posts:post_detail", kwargs={"post_id": self.post.pk}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.id, self.group_2.id)

    def test_guest_client_create_form_post(self):
        """Проверка неавторизованного пользователя на создание поста"""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Текст поста",
        }
        response = self.guest_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True
        )
        create_url = reverse("posts:post_create")
        login_url = reverse("users:login")
        self.assertRedirects(response, f"{login_url}?next={create_url}")
        self.assertEqual(Post.objects.count(), posts_count)

    def test_add_comments_by_authorized_client(self):
        """Проверка авторизованного пользователя комментировать посты."""
        self.post = Post.objects.create(
            author=self.author,
            text="Тестовый пост",
        )
        comment_count = Comment.objects.count()
        form_data = {
            "text": "Текст комментария",
        }
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True
        )
        last_comment = response.context["comments"][0]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            "posts:post_detail", kwargs={"post_id": self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(last_comment.text, form_data["text"])
