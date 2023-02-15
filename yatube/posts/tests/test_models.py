from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post, START_POST

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            pub_date="Тестовая дата",
            group=cls.group,
        )

    def test_post_model_has_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = self.post
        post_text = post.text
        self.assertEqual(str(post_text), post.text[:START_POST])

    def test_group_model_has_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = self.group
        self.assertEqual(str(group), group.title)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = self.post
        field_verboses = {
            "text": "Текст",
            "group": "Группа поста, постов",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)
