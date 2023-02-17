from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


START_POST = 15


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name="Имя группы")
    slug = models.SlugField(
        unique=True,
        verbose_name="Идентификатор"
    )
    description = models.TextField(verbose_name="Описание группы")

    class Meta:
        indexes = [
            models.Index(fields=["title", "slug", "description"]),
            models.Index(fields=["slug"], name="slug_idx"),
        ]
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст",
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор поста, постов"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        verbose_name="Группа поста, постов"
    )
    image = models.ImageField(
        "Картинка",
        upload_to="posts/",
        blank=True
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.text[:START_POST]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор комментария, комментариев"
    )
    text = models.TextField(
        verbose_name="Текст комментария"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации комментария"
    )

    class Meta:
        ordering = ["-created"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Имя подписчика",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Имя автора",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "author"],
                                    name="unique_follow")
        ]
        verbose_name = "Подписчик"
        verbose_name_plural = "Подписчики"
