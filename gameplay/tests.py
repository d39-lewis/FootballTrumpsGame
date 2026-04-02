"""
Tests for the gameplay app: models, game logic, views.
"""

import uuid
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from cards.models import Card, CollectionItem, Rarity

from .game_logic import (
    ATTRIBUTES,
    bot_pick_attribute,
    create_game,
    process_turn,
)
from .models import ActiveDeck, GameSession


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(email='player@test.com', password='pass1234'):
    return User.objects.create_user(email=email, password=password)


def make_card(**kwargs):
    defaults = dict(
        player_name='Test Player',
        rarity=Rarity.COMMON,
        finishing=50, defending=50, sprinting=50,
        strength=50, tech=50, leadership=50,
    )
    defaults.update(kwargs)
    return Card.objects.create(**defaults)


def give_15_cards(user):
    """Create 15 cards and add them to the user's collection."""
    cards = [make_card(player_name=f'Player {i}') for i in range(15)]
    for card in cards:
        CollectionItem.objects.create(user=user, card=card)
    return cards


def set_active_deck(user, cards):
    deck, _ = ActiveDeck.objects.get_or_create(user=user)
    deck.card_ids = [str(c.card_id) for c in cards]
    deck.save()
    return deck


# ── Model tests ───────────────────────────────────────────────────────────────

class ActiveDeckModelTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_is_ready_false_when_empty(self):
        deck = ActiveDeck.objects.create(user=self.user, card_ids=[])
        self.assertFalse(deck.is_ready)

    def test_is_ready_false_when_less_than_15(self):
        deck = ActiveDeck.objects.create(user=self.user, card_ids=[str(uuid.uuid4())] * 10)
        self.assertFalse(deck.is_ready)

    def test_is_ready_true_when_exactly_15(self):
        deck = ActiveDeck.objects.create(user=self.user, card_ids=[str(uuid.uuid4())] * 15)
        self.assertTrue(deck.is_ready)

    def test_is_ready_false_when_more_than_15(self):
        deck = ActiveDeck.objects.create(user=self.user, card_ids=[str(uuid.uuid4())] * 20)
        self.assertFalse(deck.is_ready)


class GameSessionModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        cards = give_15_cards(self.user)
        set_active_deck(self.user, cards)

    def test_create_game_session(self):
        session = create_game(self.user)
        self.assertEqual(session.status, GameSession.STATUS_ACTIVE)
        self.assertEqual(len(session.user_deck), 15)
        self.assertEqual(len(session.bot_deck), 15)
        self.assertIn(session.current_turn, [GameSession.TURN_USER, GameSession.TURN_BOT])

    def test_create_game_abandons_active_session(self):
        first = create_game(self.user)
        second = create_game(self.user)
        first.refresh_from_db()
        self.assertEqual(first.status, GameSession.STATUS_ABANDONED)
        self.assertEqual(second.status, GameSession.STATUS_ACTIVE)

    def test_status_choices(self):
        self.assertEqual(GameSession.STATUS_ACTIVE, 'active')
        self.assertEqual(GameSession.STATUS_WON, 'won')
        self.assertEqual(GameSession.STATUS_LOST, 'lost')
        self.assertEqual(GameSession.STATUS_ABANDONED, 'abandoned')


# ── Game logic tests ──────────────────────────────────────────────────────────

class GameLogicTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cards = give_15_cards(self.user)
        set_active_deck(self.user, self.cards)

    def test_process_turn_user_wins(self):
        """User picks finishing and has higher value."""
        user_card = make_card(player_name='UserTop', finishing=90)
        bot_card  = make_card(player_name='BotTop',  finishing=50)

        session = GameSession.objects.create(
            user=self.user,
            status=GameSession.STATUS_ACTIVE,
            user_deck=[str(user_card.card_id)] + [str(c.card_id) for c in self.cards[:14]],
            bot_deck=[str(bot_card.card_id)]  + [str(c.card_id) for c in self.cards[:14]],
            current_turn=GameSession.TURN_USER,
            round_number=1,
        )
        process_turn(session, 'finishing', picker='user')
        self.assertEqual(session.last_result['winner'], 'user')
        # Both cards go to the bottom of user's deck
        self.assertIn(str(user_card.card_id), session.user_deck)
        self.assertIn(str(bot_card.card_id), session.user_deck)

    def test_process_turn_bot_wins(self):
        """Bot picks finishing and has higher value."""
        user_card = make_card(player_name='UserTop', finishing=30)
        bot_card  = make_card(player_name='BotTop',  finishing=80)

        session = GameSession.objects.create(
            user=self.user,
            status=GameSession.STATUS_ACTIVE,
            user_deck=[str(user_card.card_id)] + [str(c.card_id) for c in self.cards[:14]],
            bot_deck=[str(bot_card.card_id)]  + [str(c.card_id) for c in self.cards[:14]],
            current_turn=GameSession.TURN_BOT,
            round_number=1,
        )
        process_turn(session, 'finishing', picker='bot')
        self.assertEqual(session.last_result['winner'], 'bot')
        self.assertIn(str(bot_card.card_id), session.bot_deck)
        self.assertIn(str(user_card.card_id), session.bot_deck)

    def test_tie_goes_to_picker_user(self):
        user_card = make_card(player_name='UserTop', finishing=70)
        bot_card  = make_card(player_name='BotTop',  finishing=70)

        session = GameSession.objects.create(
            user=self.user,
            status=GameSession.STATUS_ACTIVE,
            user_deck=[str(user_card.card_id)] + [str(c.card_id) for c in self.cards[:14]],
            bot_deck=[str(bot_card.card_id)]  + [str(c.card_id) for c in self.cards[:14]],
            current_turn=GameSession.TURN_USER,
            round_number=1,
        )
        process_turn(session, 'finishing', picker='user')
        self.assertEqual(session.last_result['winner'], 'user')

    def test_tie_goes_to_picker_bot(self):
        user_card = make_card(player_name='UserTop', finishing=70)
        bot_card  = make_card(player_name='BotTop',  finishing=70)

        session = GameSession.objects.create(
            user=self.user,
            status=GameSession.STATUS_ACTIVE,
            user_deck=[str(user_card.card_id)] + [str(c.card_id) for c in self.cards[:14]],
            bot_deck=[str(bot_card.card_id)]  + [str(c.card_id) for c in self.cards[:14]],
            current_turn=GameSession.TURN_BOT,
            round_number=1,
        )
        process_turn(session, 'finishing', picker='bot')
        self.assertEqual(session.last_result['winner'], 'bot')

    def test_game_over_user_loses(self):
        """User runs out of cards → status lost."""
        user_card = make_card(player_name='LastUser', finishing=10)
        bot_card  = make_card(player_name='BotTop',   finishing=99)

        session = GameSession.objects.create(
            user=self.user,
            status=GameSession.STATUS_ACTIVE,
            user_deck=[str(user_card.card_id)],   # only 1 card
            bot_deck=[str(bot_card.card_id)] + [str(c.card_id) for c in self.cards[:5]],
            current_turn=GameSession.TURN_BOT,
            round_number=5,
        )
        process_turn(session, 'finishing', picker='bot')
        self.assertEqual(session.status, GameSession.STATUS_LOST)

    def test_game_over_user_wins(self):
        """Bot runs out of cards → status won."""
        user_card = make_card(player_name='UserTop', finishing=99)
        bot_card  = make_card(player_name='LastBot',  finishing=10)

        session = GameSession.objects.create(
            user=self.user,
            status=GameSession.STATUS_ACTIVE,
            user_deck=[str(user_card.card_id)] + [str(c.card_id) for c in self.cards[:5]],
            bot_deck=[str(bot_card.card_id)],   # only 1 card
            current_turn=GameSession.TURN_USER,
            round_number=5,
        )
        process_turn(session, 'finishing', picker='user')
        self.assertEqual(session.status, GameSession.STATUS_WON)

    def test_round_number_increments(self):
        user_card = make_card(player_name='U', finishing=99)
        bot_card  = make_card(player_name='B', finishing=10)

        session = GameSession.objects.create(
            user=self.user,
            status=GameSession.STATUS_ACTIVE,
            user_deck=[str(user_card.card_id)] + [str(c.card_id) for c in self.cards[:5]],
            bot_deck=[str(bot_card.card_id)]  + [str(c.card_id) for c in self.cards[:5]],
            current_turn=GameSession.TURN_USER,
            round_number=3,
        )
        process_turn(session, 'finishing', picker='user')
        self.assertEqual(session.round_number, 4)

    def test_bot_pick_attribute_returns_highest(self):
        card = make_card(
            player_name='Bot', finishing=10, defending=20, sprinting=30,
            strength=40, tech=50, leadership=99
        )
        self.assertEqual(bot_pick_attribute(card), 'leadership')

    def test_bot_pick_attribute_all_equal(self):
        card = make_card(player_name='Even', finishing=50, defending=50, sprinting=50,
                         strength=50, tech=50, leadership=50)
        result = bot_pick_attribute(card)
        self.assertIn(result, ATTRIBUTES)


# ── View tests ────────────────────────────────────────────────────────────────

class DeckViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(email='player@test.com', password='pass1234')

    def test_deck_get_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('gameplay:deck'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/gameplay/deck/', resp['Location'])

    def test_deck_get_shows_cards(self):
        cards = give_15_cards(self.user)
        resp = self.client.get(reverse('gameplay:deck'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Build Your Deck')

    def test_deck_get_shows_empty_state_if_less_than_15(self):
        # User has < 15 cards
        resp = self.client.get(reverse('gameplay:deck'))
        self.assertContains(resp, 'at least 15 cards')

    def test_deck_post_saves_15_cards(self):
        cards = give_15_cards(self.user)
        card_ids = [str(c.card_id) for c in cards]
        resp = self.client.post(reverse('gameplay:deck'), {'card_ids': card_ids})
        self.assertRedirects(resp, reverse('gameplay:play'), fetch_redirect_response=False)
        deck = ActiveDeck.objects.get(user=self.user)
        self.assertTrue(deck.is_ready)

    def test_deck_post_rejects_wrong_count(self):
        cards = give_15_cards(self.user)
        card_ids = [str(c.card_id) for c in cards[:10]]
        resp = self.client.post(reverse('gameplay:deck'), {'card_ids': card_ids})
        self.assertRedirects(resp, '/gameplay/deck/?error=Select exactly 15 cards.',
                             fetch_redirect_response=False)

    def test_deck_post_rejects_unowned_cards(self):
        cards = give_15_cards(self.user)
        # Replace one ID with a foreign card
        stranger = make_card(player_name='Stranger')
        card_ids = [str(c.card_id) for c in cards[:14]] + [str(stranger.card_id)]
        resp = self.client.post(reverse('gameplay:deck'), {'card_ids': card_ids})
        self.assertRedirects(resp, '/gameplay/deck/?error=Invalid selection.',
                             fetch_redirect_response=False)


class PlayViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(email='player@test.com', password='pass1234')
        self.cards = give_15_cards(self.user)
        set_active_deck(self.user, self.cards)

    def test_play_get_creates_session(self):
        resp = self.client.get(reverse('gameplay:play'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(GameSession.objects.filter(user=self.user, status='active').exists())

    def test_play_get_redirects_without_deck(self):
        user2 = make_user(email='nodeck@test.com')
        self.client.login(email='nodeck@test.com', password='pass1234')
        resp = self.client.get(reverse('gameplay:play'))
        self.assertRedirects(resp, reverse('gameplay:deck'), fetch_redirect_response=False)

    def test_play_get_reuses_existing_session(self):
        self.client.get(reverse('gameplay:play'))
        session1 = GameSession.objects.get(user=self.user, status='active')
        self.client.get(reverse('gameplay:play'))
        session2 = GameSession.objects.get(user=self.user, status='active')
        self.assertEqual(session1.pk, session2.pk)

    def test_play_post_pick_processes_turn(self):
        self.client.get(reverse('gameplay:play'))
        session = GameSession.objects.get(user=self.user, status='active')
        session.current_turn = GameSession.TURN_USER
        session.save()

        resp = self.client.post(reverse('gameplay:play'), {
            'action': 'pick',
            'attribute': 'finishing',
        })
        self.assertIn(resp.status_code, [200, 302])

    def test_play_post_bot_play_processes_turn(self):
        self.client.get(reverse('gameplay:play'))
        session = GameSession.objects.get(user=self.user, status='active')
        session.current_turn = GameSession.TURN_BOT
        session.save()

        resp = self.client.post(reverse('gameplay:play'), {'action': 'bot_play'})
        self.assertIn(resp.status_code, [200, 302])

    def test_play_post_new_game_abandons_session(self):
        self.client.get(reverse('gameplay:play'))
        session = GameSession.objects.get(user=self.user, status='active')
        resp = self.client.post(reverse('gameplay:play'), {'action': 'new_game'})
        self.assertRedirects(resp, reverse('gameplay:deck'), fetch_redirect_response=False)
        session.refresh_from_db()
        self.assertEqual(session.status, GameSession.STATUS_ABANDONED)

    def test_play_post_win_awards_points(self):
        """Winning a game awards 100 points."""
        self.client.get(reverse('gameplay:play'))
        session = GameSession.objects.get(user=self.user, status='active')

        user_card = make_card(player_name='UTop', finishing=99)
        bot_card  = make_card(player_name='BTop', finishing=10)
        session.current_turn = GameSession.TURN_USER
        session.user_deck = [str(user_card.card_id)] + list(session.user_deck)
        session.bot_deck  = [str(bot_card.card_id)]   # only 1 card left for bot
        session.save()

        initial_points = self.user.settings.points
        self.client.post(reverse('gameplay:play'), {'action': 'pick', 'attribute': 'finishing'})
        self.user.settings.refresh_from_db()
        self.assertEqual(self.user.settings.points, initial_points + 100)

    def test_play_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('gameplay:play'))
        self.assertEqual(resp.status_code, 302)


class ResultViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(email='player@test.com', password='pass1234')
        cards = give_15_cards(self.user)
        set_active_deck(self.user, cards)

    def _make_finished_session(self, status):
        session = GameSession.objects.create(
            user=self.user,
            status=status,
            user_deck=[],
            bot_deck=[],
            current_turn=GameSession.TURN_USER,
            round_number=10,
        )
        return session

    def test_result_get_win(self):
        session = self._make_finished_session(GameSession.STATUS_WON)
        resp = self.client.get(reverse('gameplay:result', kwargs={'pk': session.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'You Won')

    def test_result_get_loss(self):
        session = self._make_finished_session(GameSession.STATUS_LOST)
        resp = self.client.get(reverse('gameplay:result', kwargs={'pk': session.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Game Over')

    def test_result_redirects_active_session(self):
        session = self._make_finished_session(GameSession.STATUS_ACTIVE)
        resp = self.client.get(reverse('gameplay:result', kwargs={'pk': session.pk}))
        self.assertRedirects(resp, reverse('gameplay:play'), fetch_redirect_response=False)

    def test_result_404_for_other_user(self):
        session = self._make_finished_session(GameSession.STATUS_WON)
        other = make_user(email='other@test.com')
        self.client.login(email='other@test.com', password='pass1234')
        resp = self.client.get(reverse('gameplay:result', kwargs={'pk': session.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_result_requires_login(self):
        session = self._make_finished_session(GameSession.STATUS_WON)
        self.client.logout()
        resp = self.client.get(reverse('gameplay:result', kwargs={'pk': session.pk}))
        self.assertEqual(resp.status_code, 302)
