"""
Comprehensive test suite for the accounts app.

Covers:
  - User model & manager
  - UserSettings model & auto-creation signal
  - PasswordResetToken model
  - All forms (Login, Register, PasswordReset*, UserSettings)
  - All views (Register, Login, Logout, PasswordReset*, UserSettings)
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import (
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    RegisterForm,
    UserSettingsForm,
)
from .models import PasswordResetToken, User, UserSettings


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def make_user(email='player@example.com', password='Str0ng!Pass', **kwargs):
    return User.objects.create_user(email=email, password=password, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# User model
# ──────────────────────────────────────────────────────────────────────────────

class UserModelTests(TestCase):

    def setUp(self):
        self.user = make_user(
            email='harry@example.com',
            first_name='Harry',
            last_name='Kane',
        )

    # Creation
    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_user_stored_with_correct_email(self):
        self.assertEqual(self.user.email, 'harry@example.com')

    def test_email_is_normalised(self):
        user = make_user(email='Test@EXAMPLE.COM')
        self.assertEqual(user.email, 'Test@example.com')

    def test_password_is_hashed(self):
        self.assertNotEqual(self.user.password, 'Str0ng!Pass')
        self.assertTrue(self.user.check_password('Str0ng!Pass'))

    def test_is_active_by_default(self):
        self.assertTrue(self.user.is_active)

    def test_is_not_staff_by_default(self):
        self.assertFalse(self.user.is_staff)

    def test_is_not_superuser_by_default(self):
        self.assertFalse(self.user.is_superuser)

    def test_date_joined_set_on_creation(self):
        self.assertIsNotNone(self.user.date_joined)

    # full_name property
    def test_full_name_first_and_last(self):
        self.assertEqual(self.user.full_name, 'Harry Kane')

    def test_full_name_first_only(self):
        user = make_user(email='a@example.com', first_name='Harry')
        self.assertEqual(user.full_name, 'Harry')

    def test_full_name_falls_back_to_email_when_blank(self):
        user = make_user(email='noname@example.com')
        self.assertEqual(user.full_name, 'noname@example.com')

    def test_str_is_email(self):
        self.assertEqual(str(self.user), 'harry@example.com')

    # Manager
    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='pass')

    def test_create_superuser_sets_is_staff(self):
        admin = User.objects.create_superuser(email='admin@example.com', password='pass')
        self.assertTrue(admin.is_staff)

    def test_create_superuser_sets_is_superuser(self):
        admin = User.objects.create_superuser(email='admin@example.com', password='pass')
        self.assertTrue(admin.is_superuser)

    def test_create_superuser_raises_if_is_staff_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='bad@example.com', password='pass', is_staff=False
            )

    def test_create_superuser_raises_if_is_superuser_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='bad@example.com', password='pass', is_superuser=False
            )

    def test_duplicate_email_raises_error(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            make_user(email='harry@example.com')


# ──────────────────────────────────────────────────────────────────────────────
# UserSettings model & signal
# ──────────────────────────────────────────────────────────────────────────────

class UserSettingsTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_settings_auto_created_on_user_save(self):
        self.assertIsInstance(self.user.settings, UserSettings)

    def test_only_one_settings_record_created(self):
        self.assertEqual(UserSettings.objects.filter(user=self.user).count(), 1)

    def test_music_enabled_true_by_default(self):
        self.assertTrue(self.user.settings.music_enabled)

    def test_settings_str(self):
        self.assertIn(self.user.email, str(self.user.settings))

    def test_settings_cascade_deleted_with_user(self):
        settings_pk = self.user.settings.pk
        self.user.delete()
        self.assertFalse(UserSettings.objects.filter(pk=settings_pk).exists())

    def test_music_can_be_disabled(self):
        self.user.settings.music_enabled = False
        self.user.settings.save()
        self.user.settings.refresh_from_db()
        self.assertFalse(self.user.settings.music_enabled)

    def test_points_default_500_on_signup(self):
        self.assertEqual(self.user.settings.points, 500)

    def test_points_can_be_updated(self):
        self.user.settings.points = 350
        self.user.settings.save()
        self.user.settings.refresh_from_db()
        self.assertEqual(self.user.settings.points, 350)

    def test_each_new_user_gets_500_points(self):
        user2 = make_user(email='player2@example.com')
        self.assertEqual(user2.settings.points, 500)


# ──────────────────────────────────────────────────────────────────────────────
# PasswordResetToken model
# ──────────────────────────────────────────────────────────────────────────────

class PasswordResetTokenTests(TestCase):

    def setUp(self):
        self.user = make_user(email='reset@example.com')

    def test_token_uuid_auto_generated(self):
        token = PasswordResetToken.objects.create(user=self.user)
        self.assertIsNotNone(token.token)

    def test_two_tokens_have_different_uuids(self):
        t1 = PasswordResetToken.objects.create(user=self.user)
        t2 = PasswordResetToken.objects.create(user=self.user)
        self.assertNotEqual(t1.token, t2.token)

    def test_expires_at_set_automatically(self):
        token = PasswordResetToken.objects.create(user=self.user)
        self.assertIsNotNone(token.expires_at)

    def test_expires_at_is_24_hours_from_now(self):
        before = timezone.now()
        token = PasswordResetToken.objects.create(user=self.user)
        after = timezone.now()
        delta = token.expires_at - before
        self.assertGreaterEqual(delta.total_seconds(), 23 * 3600)
        delta2 = token.expires_at - after
        self.assertLessEqual(delta2.total_seconds(), 24 * 3600)

    def test_is_unused_by_default(self):
        token = PasswordResetToken.objects.create(user=self.user)
        self.assertFalse(token.is_used)

    def test_is_valid_when_fresh(self):
        token = PasswordResetToken.objects.create(user=self.user)
        self.assertTrue(token.is_valid)

    def test_is_invalid_after_consume(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token.consume()
        self.assertFalse(token.is_valid)

    def test_consume_sets_is_used_true(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token.consume()
        token.refresh_from_db()
        self.assertTrue(token.is_used)

    def test_is_invalid_when_expired(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        token.save()
        self.assertFalse(token.is_valid)

    def test_is_invalid_when_used_and_not_expired(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token.consume()
        self.assertFalse(token.is_valid)

    def test_token_str_contains_email(self):
        token = PasswordResetToken.objects.create(user=self.user)
        self.assertIn(self.user.email, str(token))

    def test_token_cascade_deleted_with_user(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token_pk = token.pk
        self.user.delete()
        self.assertFalse(PasswordResetToken.objects.filter(pk=token_pk).exists())


# ──────────────────────────────────────────────────────────────────────────────
# Forms
# ──────────────────────────────────────────────────────────────────────────────

class LoginFormTests(TestCase):

    def setUp(self):
        self.user = make_user(email='login@example.com', password='Str0ng!Pass')

    def test_valid_credentials_are_accepted(self):
        form = LoginForm(data={'email': 'login@example.com', 'password': 'Str0ng!Pass'})
        self.assertTrue(form.is_valid())

    def test_wrong_password_is_rejected(self):
        form = LoginForm(data={'email': 'login@example.com', 'password': 'wrong'})
        self.assertFalse(form.is_valid())

    def test_unknown_email_is_rejected(self):
        form = LoginForm(data={'email': 'nobody@example.com', 'password': 'Str0ng!Pass'})
        self.assertFalse(form.is_valid())

    def test_inactive_user_is_rejected(self):
        self.user.is_active = False
        self.user.save()
        form = LoginForm(data={'email': 'login@example.com', 'password': 'Str0ng!Pass'})
        self.assertFalse(form.is_valid())

    def test_get_user_returns_user_on_success(self):
        form = LoginForm(data={'email': 'login@example.com', 'password': 'Str0ng!Pass'})
        form.is_valid()
        self.assertEqual(form.get_user(), self.user)

    def test_missing_email_is_invalid(self):
        form = LoginForm(data={'password': 'Str0ng!Pass'})
        self.assertFalse(form.is_valid())

    def test_missing_password_is_invalid(self):
        form = LoginForm(data={'email': 'login@example.com'})
        self.assertFalse(form.is_valid())


class RegisterFormTests(TestCase):

    def _valid_data(self, **overrides):
        data = {
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'Str0ng!Pass',
            'password_confirm': 'Str0ng!Pass',
        }
        data.update(overrides)
        return data

    def test_valid_data_is_accepted(self):
        form = RegisterForm(data=self._valid_data())
        self.assertTrue(form.is_valid())

    def test_mismatched_passwords_rejected(self):
        form = RegisterForm(data=self._valid_data(password_confirm='Different1!'))
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)

    def test_duplicate_email_rejected(self):
        make_user(email='new@example.com')
        form = RegisterForm(data=self._valid_data())
        self.assertFalse(form.is_valid())

    def test_save_creates_user_with_hashed_password(self):
        form = RegisterForm(data=self._valid_data())
        form.is_valid()
        user = form.save()
        self.assertTrue(user.check_password('Str0ng!Pass'))

    def test_save_does_not_store_plaintext_password(self):
        form = RegisterForm(data=self._valid_data())
        form.is_valid()
        user = form.save()
        self.assertNotEqual(user.password, 'Str0ng!Pass')

    def test_invalid_email_format_rejected(self):
        form = RegisterForm(data=self._valid_data(email='not-an-email'))
        self.assertFalse(form.is_valid())


class PasswordResetConfirmFormTests(TestCase):

    def test_matching_passwords_valid(self):
        form = PasswordResetConfirmForm(data={
            'password': 'NewStr0ng!Pass',
            'password_confirm': 'NewStr0ng!Pass',
        })
        self.assertTrue(form.is_valid())

    def test_mismatched_passwords_invalid(self):
        form = PasswordResetConfirmForm(data={
            'password': 'NewStr0ng!Pass',
            'password_confirm': 'Different1!',
        })
        self.assertFalse(form.is_valid())

    def test_missing_password_invalid(self):
        form = PasswordResetConfirmForm(data={'password_confirm': 'NewStr0ng!Pass'})
        self.assertFalse(form.is_valid())


class UserSettingsFormTests(TestCase):

    def test_music_enabled_true(self):
        form = UserSettingsForm(data={'music_enabled': True})
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data['music_enabled'])

    def test_music_enabled_false(self):
        form = UserSettingsForm(data={})
        self.assertTrue(form.is_valid())
        self.assertFalse(form.cleaned_data['music_enabled'])


# ──────────────────────────────────────────────────────────────────────────────
# Views
# ──────────────────────────────────────────────────────────────────────────────

class RegisterViewTests(TestCase):

    URL = '/accounts/register/'

    def _post(self, **overrides):
        data = {
            'email': 'signup@example.com',
            'first_name': 'Sign',
            'last_name': 'Up',
            'password': 'Str0ng!Pass',
            'password_confirm': 'Str0ng!Pass',
        }
        data.update(overrides)
        return self.client.post(self.URL, data)

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_get_contains_form(self):
        response = self.client.get(self.URL)
        self.assertIn('form', response.context)

    def test_valid_post_creates_user(self):
        self._post()
        self.assertTrue(User.objects.filter(email='signup@example.com').exists())

    def test_valid_post_redirects_to_home(self):
        response = self._post()
        self.assertRedirects(response, '/home/')

    def test_valid_post_logs_user_in(self):
        self._post()
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)

    def test_invalid_post_does_not_create_user(self):
        self._post(password_confirm='Mismatch1!')
        self.assertFalse(User.objects.filter(email='signup@example.com').exists())

    def test_invalid_post_returns_200_with_errors(self):
        response = self._post(password_confirm='Mismatch1!')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_duplicate_email_shows_error(self):
        make_user(email='signup@example.com')
        response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)


class LoginViewTests(TestCase):

    URL = '/accounts/login/'

    def setUp(self):
        self.user = make_user(email='login@example.com', password='Str0ng!Pass')

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_get_contains_form(self):
        response = self.client.get(self.URL)
        self.assertIn('form', response.context)

    def test_valid_login_redirects_to_home(self):
        response = self.client.post(
            self.URL, {'email': 'login@example.com', 'password': 'Str0ng!Pass'}
        )
        self.assertRedirects(response, '/home/')

    def test_invalid_password_returns_200(self):
        response = self.client.post(
            self.URL, {'email': 'login@example.com', 'password': 'wrong'}
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_password_shows_form_error(self):
        response = self.client.post(
            self.URL, {'email': 'login@example.com', 'password': 'wrong'}
        )
        self.assertFormError(response.context['form'], None, 'Invalid email or password.')

    def test_unknown_email_returns_200(self):
        response = self.client.post(
            self.URL, {'email': 'ghost@example.com', 'password': 'Str0ng!Pass'}
        )
        self.assertEqual(response.status_code, 200)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            self.URL, {'email': 'login@example.com', 'password': 'Str0ng!Pass'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)


class LogoutViewTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_post_logs_user_out(self):
        self.client.post('/accounts/logout/')
        response = self.client.get('/home/')
        self.assertNotEqual(response.status_code, 200)

    def test_post_redirects_to_landing(self):
        response = self.client.post('/accounts/logout/')
        self.assertRedirects(response, '/')

    def test_get_not_allowed(self):
        response = self.client.get('/accounts/logout/')
        self.assertEqual(response.status_code, 405)


class PasswordResetRequestViewTests(TestCase):

    URL = '/accounts/password-reset/'

    def setUp(self):
        self.user = make_user(email='reset@example.com')

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_valid_email_creates_token(self):
        self.client.post(self.URL, {'email': 'reset@example.com'})
        self.assertEqual(PasswordResetToken.objects.filter(user=self.user).count(), 1)

    def test_unknown_email_does_not_create_token(self):
        self.client.post(self.URL, {'email': 'nobody@example.com'})
        self.assertEqual(PasswordResetToken.objects.count(), 0)

    def test_unknown_email_shows_same_message(self):
        """Don't reveal whether an email is registered."""
        response = self.client.post(
            self.URL, {'email': 'nobody@example.com'}, follow=True
        )
        messages = list(response.context['messages'])
        self.assertTrue(any('reset link' in str(m) for m in messages))

    def test_inactive_user_does_not_get_token(self):
        self.user.is_active = False
        self.user.save()
        self.client.post(self.URL, {'email': 'reset@example.com'})
        self.assertEqual(PasswordResetToken.objects.count(), 0)


class PasswordResetConfirmViewTests(TestCase):

    def setUp(self):
        self.user = make_user(email='confirm@example.com', password='OldPass1!')
        self.token = PasswordResetToken.objects.create(user=self.user)
        self.url = f'/accounts/password-reset/{self.token.token}/'

    def test_get_valid_token_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_get_invalid_uuid_returns_404(self):
        import uuid
        response = self.client.get(f'/accounts/password-reset/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, 404)

    def test_get_expired_token_redirects(self):
        self.token.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        self.token.save()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/accounts/password-reset/')

    def test_get_used_token_redirects(self):
        self.token.consume()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/accounts/password-reset/')

    def test_valid_post_changes_password(self):
        self.client.post(self.url, {
            'password': 'NewStr0ng!Pass',
            'password_confirm': 'NewStr0ng!Pass',
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStr0ng!Pass'))

    def test_valid_post_consumes_token(self):
        self.client.post(self.url, {
            'password': 'NewStr0ng!Pass',
            'password_confirm': 'NewStr0ng!Pass',
        })
        self.token.refresh_from_db()
        self.assertTrue(self.token.is_used)

    def test_valid_post_redirects_to_login(self):
        response = self.client.post(self.url, {
            'password': 'NewStr0ng!Pass',
            'password_confirm': 'NewStr0ng!Pass',
        })
        self.assertRedirects(response, '/accounts/login/')

    def test_mismatched_passwords_does_not_change_password(self):
        self.client.post(self.url, {
            'password': 'NewStr0ng!Pass',
            'password_confirm': 'Different1!',
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass1!'))

    def test_used_token_cannot_be_reused(self):
        payload = {'password': 'NewStr0ng!Pass', 'password_confirm': 'NewStr0ng!Pass'}
        self.client.post(self.url, payload)
        response = self.client.post(self.url, payload)
        self.assertRedirects(response, '/accounts/password-reset/')


class UserSettingsViewTests(TestCase):

    URL = '/accounts/settings/'

    def setUp(self):
        self.user = make_user()

    def test_get_requires_login(self):
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response['Location'])

    def test_get_returns_200_when_logged_in(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_get_contains_form(self):
        self.client.force_login(self.user)
        response = self.client.get(self.URL)
        self.assertIn('form', response.context)

    def test_post_saves_music_disabled(self):
        self.client.force_login(self.user)
        self.client.post(self.URL, {})
        self.user.settings.refresh_from_db()
        self.assertFalse(self.user.settings.music_enabled)

    def test_post_saves_music_enabled(self):
        self.client.force_login(self.user)
        self.client.post(self.URL, {'music_enabled': True})
        self.user.settings.refresh_from_db()
        self.assertTrue(self.user.settings.music_enabled)

    def test_post_redirects_to_home(self):
        self.client.force_login(self.user)
        response = self.client.post(self.URL, {'music_enabled': True})
        self.assertRedirects(response, '/home/')


class LandingAndHomeViewTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_landing_returns_200_when_not_logged_in(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_landing_returns_200_when_logged_in(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_home_requires_login(self):
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 302)

    def test_home_returns_200_when_logged_in(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/home/').status_code, 200)

    def test_home_shows_500_points_for_new_user(self):
        self.client.force_login(self.user)
        response = self.client.get('/home/')
        self.assertEqual(response.context['points'], 500)

    def test_home_points_reflect_updated_value(self):
        self.user.settings.points = 250
        self.user.settings.save()
        self.client.force_login(self.user)
        response = self.client.get('/home/')
        self.assertEqual(response.context['points'], 250)
