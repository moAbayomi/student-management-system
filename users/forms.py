from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django import forms

INPUT_CLASSES = "w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-gray-900 focus:ring-1 focus:ring-gray-900 bg-slate-50/50 transition-all text-sm text-black"

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(LoginForm, self).__init__(*args, **kwargs)

   
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-gray-900 transition-colors',
            'placeholder': 'Username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-gray-900 transition-colors',
            'placeholder': 'Password',
        })
    )

class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': 'Enter your registered email'
        })

class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': INPUT_CLASSES,
                'placeholder': '••••••••'
            })