from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .models import Comment, Follow, Group, Post, User
from .forms import PostForm, CommentForm
from .utils import paginate


CACHE_TIME = 20


@cache_page(CACHE_TIME, key_prefix="index_page")
def index(request):
    posts = Post.objects.select_related("author", "group")
    page_obj = paginate(request, posts)
    context = {
        "posts": posts,
        "page_obj": page_obj,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginate(request, posts)
    context = {
        "group": group,
        "posts": posts,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    post_count = posts.count()
    page_obj = paginate(request, posts)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()
    context = {
        "author": author,
        "page_obj": page_obj,
        "post_count": post_count,
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post_count = Post.objects.select_related("author").count()
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post_id=post.id)
    context = {
        "post": post,
        "post_count": post_count,
        "form": form,
        "comments": comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect("posts:profile", post.author)
        else:
            return render(
                request, "posts/create_or_update_post.html", {"form": form})
    else:
        form = PostForm()
        return render(
            request, "posts/create_or_update_post.html", {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if request.user != post.author:
        return redirect("posts:post_detail", post_id)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    return render(
        request, "posts/create_or_update_post.html",
        {"form": form,
         "is_edit": True}
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate(request, posts)
    context = {
        "posts": posts,
        "page_obj": page_obj,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if request.user != user:
        Follow.objects.get_or_create(
            user_id=request.user.id,
            author_id=user.id
        )
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    Follow.objects.filter(user_id=request.user.id, author_id=user.id).delete()
    return redirect("posts:profile", username=username)
