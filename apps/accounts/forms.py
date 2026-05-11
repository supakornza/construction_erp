from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import User, UserProfile


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone', 'profile_photo', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('username', css_class='col-md-6'), Column('email', css_class='col-md-6')),
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            Row(Column('role', css_class='col-md-6'), Column('phone', css_class='col-md-6')),
            'profile_photo',
            Row(Column('password1', css_class='col-md-6'), Column('password2', css_class='col-md-6')),
            Submit('submit', 'Create User', css_class='btn btn-primary'),
        )


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'phone', 'profile_photo', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            Row(Column('email', css_class='col-md-6'), Column('phone', css_class='col-md-6')),
            Row(Column('role', css_class='col-md-6'), Column('is_active', css_class='col-md-6')),
            'profile_photo',
            Submit('submit', 'Update User', css_class='btn btn-primary'),
        )


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = UserProfile
        fields = ['company', 'position', 'signature']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.user.phone
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            Row(Column('email', css_class='col-md-6'), Column('phone', css_class='col-md-6')),
            Row(Column('company', css_class='col-md-6'), Column('position', css_class='col-md-6')),
            'signature',
            Submit('submit', 'Save Profile', css_class='btn btn-primary'),
        )

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
            profile.save()
        return profile
