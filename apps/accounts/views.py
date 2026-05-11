from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, FormView, View
from .models import User, UserProfile
from .forms import UserCreateForm, UserUpdateForm, ProfileForm
from .mixins import AdminRequiredMixin


class LoginView(FormView):
    template_name = 'registration/login.html'
    form_class = AuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect(self.request.GET.get('next', 'dashboard:index'))


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('accounts:login')

    def get(self, request):
        logout(request)
        return redirect('accounts:login')


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(username__icontains=q) | qs.filter(email__icontains=q)
        return qs


class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        UserProfile.objects.get_or_create(user=self.object)
        messages.success(self.request, f'User {self.object.username} created successfully.')
        return response


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        messages.success(self.request, 'User updated successfully.')
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)


class UserDetailView(AdminRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'viewed_user'
