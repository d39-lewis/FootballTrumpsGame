from django.test import TestCase
from django.utils import timezone

from .models import PasswordResetToken, User, UserSettings


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='player@example.com',
            password='Str0ng!Pass',
            first_name='Harry',
            last_name='Kane',
        )

    def test_user_created_with_email(self):
        self.assertEqual(self.user.email, 'player@example.com')

    def test_full_name(self):
        self.assertEqual(self.user.full_name, 'Harry Kane')

    def test_full_name_falls_back_to_email(self):
        user = User.objects.create_user(email='noname@example.com', password='pass')
        self.assertEqual(user.full_name, 'noname@example.com')

    def test_user_settings_created_automatically(self):
        self.assertTrue(hasattr(self.user, 'settings'))
        self.assertIsInstance(self.user.settings, UserSettings)

    def test_default_music_enabled(self):
        self.assertTrue(self.user.settings.music_enabled)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email='admin@example.com', password='admin')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class PasswordResetTokenTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='reset@example.com', password='pass')

    def test_token_is_valid_on_creation(self):
        token = PasswordResetToken.objects.create(user=self.user)
        self.assertTrue(token.is_valid)

    def test_consume_invalidates_token(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token.consume()
        self.assertFalse(token.is_valid)

    def test_expired_token_is_invalid(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        token.save()
        self.assertFalse(token.is_valid)

    def test_token_deleted_when_user_deleted(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token_pk = token.pk
        self.user.delete()
        self.assertFalse(PasswordResetToken.objects.filter(pk=token_pk).exists())


class AuthViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='view@example.com', password='Str0ng!Pass')

    def test_login_page_loads(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_register_page_loads(self):
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirects(self):
        response = self.client.post(
            '/accounts/login/',
            {'email': 'view@example.com', 'password': 'Str0ng!Pass'},
        )
        self.assertRedirects(response, '/accounts/settings/')

    def test_invalid_login_shows_error(self):
        response = self.client.post(
            '/accounts/login/',
            {'email': 'view@example.com', 'password': 'wrongpass'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], None, 'Invalid email or password.')

    def test_settings_requires_login(self):
        response = self.client.get('/accounts/settings/')
        self.assertRedirects(response, '/accounts/login/?next=/accounts/settings/')

    def test_settings_accessible_when_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get('/accounts/settings/')
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects_to_login(self):
        self.client.force_login(self.user)
        response = self.client.post('/accounts/logout/')
        self.assertRedirects(response, '/accounts/login/')

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(
            '/accounts/register/',
            {
                'email': 'new@example.com',
                'first_name': 'New',
                'last_name': 'Player',
                'password': 'Str0ng!Pass',
                'password_confirm': 'Str0ng!Pass',
            },
        )
        self.assertTrue(User.objects.filter(email='new@example.com').exists())
        self.assertRedirects(response, '/accounts/settings/')
