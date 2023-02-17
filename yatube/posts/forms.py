from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        labels = {"text": "Введите текст", "group": "Выберите группу"}
        help_texts = {
            "text": "Текст нового поста",
            "group": "Группа, к которой будет относится пост",
        }
        error_messages = {"text": {"required": "Обязательно для заполнения"}}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
