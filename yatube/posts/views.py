from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings

from .models import Post, Group, Follow, User
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.select_related('group', 'author')
    paginator = Paginator(post_list, settings.MAX_PAGE_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    paginator = Paginator(post_list, settings.MAX_PAGE_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    paginator = Paginator(post_list, settings.MAX_PAGE_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = request.user.is_authenticated and author.following.exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('group', 'author'),
                             id=post_id)
    count = post.author.posts.count()
    comments = post.comments.select_related('author')
    form = CommentForm(request.POST or None)
    context = {
        'comments': comments,
        'post': post,
        'count': count,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/form_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post.objects.select_related('group', 'author'),
                             id=post_id)
    if request.user == post.author:
        form = PostForm(request.POST or None,
                        files=request.FILES or None,
                        instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
        context = {
            'form': form,
            'is_edit': True,
        }
        return render(request, 'posts/form_post.html', context)
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.MAX_PAGE_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(
        flake8user=request.user, author=author).exists()
    if request.user != author and not follow_check:
        Follow.objects.create(
            user=request.user,
            author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(
        user=request.user, author=author).exists()
    if request.user != author and follow_check:
        Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('posts:profile', username=username)
