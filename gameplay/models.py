from django.conf import settings
from django.db import models


class ActiveDeck(models.Model):
    """
    The 15 cards a user has chosen as their active playing deck.
    Stored as an ordered list of card_id strings.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='active_deck',
    )
    card_ids = models.JSONField(default=list)   # [str(uuid), ...]
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'ActiveDeck for {self.user.email} ({len(self.card_ids)} cards)'

    @property
    def is_ready(self):
        return len(self.card_ids) == 15


class GameSession(models.Model):
    """
    A single game of Football Trumps between a user and the bot.
    Decks are stored as ordered JSON lists — index 0 is the top card.
    """
    STATUS_ACTIVE    = 'active'
    STATUS_WON       = 'won'
    STATUS_LOST      = 'lost'
    STATUS_ABANDONED = 'abandoned'

    STATUS_CHOICES = [
        (STATUS_ACTIVE,    'Active'),
        (STATUS_WON,       'Won'),
        (STATUS_LOST,      'Lost'),
        (STATUS_ABANDONED, 'Abandoned'),
    ]

    TURN_USER = 'user'
    TURN_BOT  = 'bot'
    TURN_CHOICES = [(TURN_USER, 'User'), (TURN_BOT, 'Bot')]

    user         = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_sessions',
    )
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    user_deck    = models.JSONField()   # [str(uuid), ...]
    bot_deck     = models.JSONField()   # [str(uuid), ...]
    current_turn = models.CharField(max_length=5, choices=TURN_CHOICES, default=TURN_USER)
    last_result  = models.JSONField(null=True, blank=True)
    round_number = models.PositiveIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Game #{self.pk} — {self.user.email} ({self.status})'
