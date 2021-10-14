from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.generic.edit import CreateView, UpdateView

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def set_pagination(request, obj_list, amount=settings.PAGE_SIZE):
    paginator = Paginator(obj_list, amount)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20)
def index(request):
    template = 'posts/index.html'

    post_list = Post.objects.all()
    page_obj = set_pagination(request, post_list)

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)

    post_list = group.posts.all()
    page_obj = set_pagination(request, post_list)

    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = User.objects.get(username=username)

    post_list = author.posts.all()
    page_obj = set_pagination(request, post_list)

    is_following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user, author=author).exists():
            is_following = True

    context = {
        'page_obj': page_obj,
        'author': author,
        'following': is_following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    specific_post = get_object_or_404(Post, pk=post_id)

    page_obj = specific_post.author.posts.all()

    comments_list = specific_post.comments.all()
    form = CommentForm()

    context = {
        'post': specific_post,
        'page_obj': page_obj,
        'comments': comments_list,
        'form': form,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'

    post_list = Post.objects.filter(author__following__user=request.user)
    no_follow = (post_list.count() == 0)

    page_obj = set_pagination(request, post_list)

    context = {
        'page_obj': page_obj,
        'no_follow': no_follow,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)

    return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()

    return redirect('posts:index')


class PostCreate(LoginRequiredMixin, CreateView):
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def get_context_data(self, **kwargs):
        context = super(PostCreate, self).get_context_data(**kwargs)
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        form.instance = form.save(commit=False)
        form.instance.author = self.request.user
        form.instance.save()

        success_url = reverse(
            'posts:profile',
            kwargs={'username': self.request.user.username}
        )

        return redirect(success_url)


class PostEdit(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user

    def handle_no_permission(self):
        return redirect(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        ))

    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])

    def get_context_data(self, **kwargs):
        context = super(PostEdit, self).get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        form.instance.save()

        success_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.object.pk}
        )

        return redirect(success_url)
