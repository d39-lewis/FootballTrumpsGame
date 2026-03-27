from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from .forms import (
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    RegisterForm,
    UserSettingsForm,
)
from .models import PasswordResetToken, User


class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('home')
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('landing')


class PasswordResetRequestView(View):
    template_name = 'accounts/password_reset_request.html'

    def get(self, request):
        return render(request, self.template_name, {'form': PasswordResetRequestForm()})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email, is_active=True)
                token = PasswordResetToken.objects.create(user=user)
                reset_url = request.build_absolute_uri(
                    reverse('accounts:password_reset_confirm', args=[token.token])
                )
                print(f'\n[PASSWORD RESET] {email} → {reset_url}\n')
            except User.DoesNotExist:
                pass  # Don't reveal whether the email exists
            messages.info(
                request,
                'If that email is registered you will receive a reset link shortly.',
            )
            return redirect('accounts:password_reset_request')
        return render(request, self.template_name, {'form': form})


class PasswordResetConfirmView(View):
    template_name = 'accounts/password_reset_confirm.html'

    def _get_valid_token(self, token_uuid):
        token = get_object_or_404(PasswordResetToken, token=token_uuid)
        if not token.is_valid:
            return None
        return token

    def get(self, request, token):
        reset_token = self._get_valid_token(token)
        if reset_token is None:
            messages.error(request, 'This reset link is invalid or has expired.')
            return redirect('accounts:password_reset_request')
        return render(request, self.template_name, {'form': PasswordResetConfirmForm()})

    def post(self, request, token):
        reset_token = self._get_valid_token(token)
        if reset_token is None:
            messages.error(request, 'This reset link is invalid or has expired.')
            return redirect('accounts:password_reset_request')

        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            user = reset_token.user
            user.set_password(form.cleaned_data['password'])
            user.save(update_fields=['password'])
            reset_token.consume()
            messages.success(request, 'Password updated. You can now log in.')
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class UserSettingsView(View):
    template_name = 'accounts/settings.html'

    def get(self, request):
        settings = request.user.settings
        form = UserSettingsForm(initial={'music_enabled': settings.music_enabled})
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserSettingsForm(request.POST)
        if form.is_valid():
            settings = request.user.settings
            settings.music_enabled = form.cleaned_data['music_enabled']
            settings.save(update_fields=['music_enabled'])
            return redirect('home')
        return render(request, self.template_name, {'form': form})
