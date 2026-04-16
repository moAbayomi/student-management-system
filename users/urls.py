from django.urls import path, reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from .forms import LoginForm, StyledPasswordResetForm, StyledSetPasswordForm

app_name = 'users'

urlpatterns = [
    path('login/', LoginView.as_view(
        template_name='users/login.html',
        authentication_form=LoginForm,
    ), name='login'),

    path('logout/', 
         LogoutView.as_view(), 
         name='logout'),

    path('password-reset/', PasswordResetView.as_view(
        template_name='users/password_reset.html',
        form_class=StyledPasswordResetForm,
        success_url=reverse_lazy('users:password_reset_done'),
        email_template_name='users/password_reset_email.html'
    ), name='password_reset'),

    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        form_class=StyledSetPasswordForm,  
        success_url=reverse_lazy('users:password_reset_complete') 
    ), name='password_reset_confirm'),

    path('password-reset-complete/', PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
]