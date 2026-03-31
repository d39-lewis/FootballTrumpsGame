import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email as the primary identifier instead of username.
    Owns identity and authentication for the entire project.
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email + password are prompted by default

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email


class PasswordResetToken(models.Model):
    """
    Single-use token for the password reset flow.
    Tokens expire after TOKEN_LIFETIME_HOURS and are invalidated on use.
    """

    TOKEN_LIFETIME_HOURS = 24

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'password reset token'
        verbose_name_plural = 'password reset tokens'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=self.TOKEN_LIFETIME_HOURS)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'PasswordResetToken for {self.user.email} (used={self.is_used})'

    @property
    def is_valid(self):
        """Returns True if the token has not been used and has not expired."""
        return not self.is_used and timezone.now() < self.expires_at

    def consume(self):
        """Mark this token as used. Call this after a successful password reset."""
        self.is_used = True
        self.save(update_fields=['is_used'])


class UserSettings(models.Model):
    """
    Per-user preferences. Created automatically when a User is created (via signal).
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings',
    )
    music_enabled = models.BooleanField(default=True)
    points = models.PositiveIntegerField(default=500)

    class Meta:
        verbose_name = 'user settings'
        verbose_name_plural = 'user settings'

    def __str__(self):
        return f'Settings for {self.user.email}'
