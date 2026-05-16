from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
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
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(1209600)  # 14 days
        return redirect(self.request.GET.get('next', 'dashboard:index'))


class ChangePasswordView(LoginRequiredMixin, FormView):
    template_name = 'registration/password_change_form.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('accounts:profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, 'เปลี่ยนรหัสผ่านเรียบร้อยแล้ว')
        return super().form_valid(form)


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


class RoleListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/role_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.all().order_by('role', 'username')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        users_by_role = {}
        for role_value, role_label in User.ROLE_CHOICES:
            users_by_role[role_value] = {
                'label': role_label,
                'users': [],
            }
        for u in ctx['users']:
            if u.role in users_by_role:
                users_by_role[u.role]['users'].append(u)
        ctx['users_by_role'] = users_by_role
        ctx['role_choices'] = User.ROLE_CHOICES
        return ctx


class UserRoleUpdateView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        new_role = request.POST.get('role')
        valid_roles = {r[0] for r in User.ROLE_CHOICES}
        if new_role in valid_roles:
            user.role = new_role
            user.save(update_fields=['role'])
            messages.success(request, f'{user.username} role updated to {user.get_role_display()}.')
        else:
            messages.error(request, 'Invalid role.')
        return redirect(request.POST.get('next', 'accounts:role_list'))
