from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

CACHE_TIMEOUT_INDEX = 20


def paginate_page(request, posts):
    paginator = Paginator(posts, settings.COUNT_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@cache_page(CACHE_TIMEOUT_INDEX, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related("author", "group")
    context = {
        "page_obj": paginate_page(request, posts)
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("author", "group")
    context = {
        "group": group,
        "page_obj": paginate_page(request, posts)
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related("author", "group")
    following = (request.user.is_authenticated
                 and author.following.filter(user=request.user).exists())
    context = {
        "author": author,
        "page_obj": paginate_page(request, posts),
        "following": following
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.select_related("author")
    if request.method == "POST" and form.is_valid():
        add_comment(request, post_id=post.pk)
    context = {
        "post": post,
        "form": form,
        "comments": comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect("posts:profile", request.user.username)
    context = {
        "form": form,
        "is_edit": False
    }
    return render(request, "posts/create_post.html", context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def follow_index(request):
    posts = Post.objects.select_related(
        "author", "group").filter(author__following__user=request.user)
    context = {
        "page_obj": paginate_page(request, posts),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect("posts:follow_index")


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    author.following.filter(user=request.user).delete()
    return redirect("posts:follow_index")
