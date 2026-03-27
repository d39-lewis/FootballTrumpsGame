import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Rarity(models.TextChoices):
    COMMON = 'common', 'Common'
    RARE = 'rare', 'Rare'
    ULTRA_RARE = 'ultra_rare', 'Ultra Rare'
    EPIC = 'epic', 'Epic'
    LEGENDARY = 'legendary', 'Legendary'


class Card(models.Model):
    """
    A single football player card in the catalogue.
    This record is shared across all users — it is never duplicated.
    """

    card_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    player_name = models.CharField(max_length=100)
    image_url = models.URLField(
        blank=True,
        help_text='URL of the AI-generated card artwork.',
    )
    rarity = models.CharField(
        max_length=20,
        choices=Rarity.choices,
        default=Rarity.COMMON,
        db_index=True,
    )

    # ── Gameplay attributes (0–99) ──────────────────────────────────────────
    finishing = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)],
    )
    defending = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)],
    )
    sprinting = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)],
    )
    strength = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)],
    )
    tech = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)],
    )
    leadership = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)],
    )

    class Meta:
        verbose_name = 'card'
        verbose_name_plural = 'cards'
        ordering = ['rarity', 'player_name']

    def __str__(self):
        return f'{self.player_name} ({self.get_rarity_display()})'

    @property
    def stats(self):
        """Return all six gameplay stats as a dict."""
        return {
            'finishing': self.finishing,
            'defending': self.defending,
            'sprinting': self.sprinting,
            'strength': self.strength,
            'tech': self.tech,
            'leadership': self.leadership,
        }

    @property
    def overall(self):
        """Average of all six stats — useful for display."""
        return round(sum(self.stats.values()) / 6)


class CollectionItem(models.Model):
    """
    Tracks how many copies of a card a user owns.
    If a user receives a duplicate, quantity is incremented rather than
    creating a new record.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collection',
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name='collection_items',
    )
    quantity = models.PositiveIntegerField(default=1)
    date_obtained = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'collection item'
        verbose_name_plural = 'collection items'
        unique_together = ('user', 'card')
        ordering = ['-date_obtained']

    def __str__(self):
        return f'{self.user.email} — {self.card.player_name} x{self.quantity}'

    @classmethod
    def add_to_collection(cls, user, card):
        """
        Add one copy of a card to a user's collection.
        Creates the record if it doesn't exist, otherwise increments quantity.
        Returns the CollectionItem and a boolean indicating if it was created.
        """
        item, created = cls.objects.get_or_create(
            user=user,
            card=card,
            defaults={'quantity': 1},
        )
        if not created:
            item.quantity += 1
            item.save(update_fields=['quantity'])
        return item, created
