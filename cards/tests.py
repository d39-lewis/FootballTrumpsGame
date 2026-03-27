"""
Comprehensive test suite for the cards app.

Covers:
  - Card model (UUID pk, stats, overall, rarity choices, ordering, str)
  - CollectionItem model (add_to_collection, duplicates, cascade deletes)
  - CollectionView (rarity selector page)
  - RarityDetailView (per-rarity card list)
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from cards.models import Card, CollectionItem, Rarity


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def make_user(email='user@example.com', password='pass'):
    return User.objects.create_user(email=email, password=password)


def make_card(**kwargs):
    defaults = dict(
        player_name='Test Player',
        rarity=Rarity.COMMON,
        finishing=50,
        defending=50,
        sprinting=50,
        strength=50,
        tech=50,
        leadership=50,
    )
    defaults.update(kwargs)
    return Card.objects.create(**defaults)


# ──────────────────────────────────────────────────────────────────────────────
# Card model
# ──────────────────────────────────────────────────────────────────────────────

class CardModelTests(TestCase):

    # Identity
    def test_card_id_is_uuid_and_auto_generated(self):
        import uuid
        card = make_card()
        self.assertIsInstance(card.card_id, uuid.UUID)

    def test_two_cards_have_different_uuids(self):
        c1 = make_card(player_name='A')
        c2 = make_card(player_name='B')
        self.assertNotEqual(c1.card_id, c2.card_id)

    def test_str_includes_name_and_rarity(self):
        card = make_card(player_name='Messi', rarity=Rarity.LEGENDARY)
        self.assertEqual(str(card), 'Messi (Legendary)')

    def test_str_common_rarity(self):
        card = make_card(player_name='Player', rarity=Rarity.COMMON)
        self.assertEqual(str(card), 'Player (Common)')

    # Rarity choices
    def test_all_rarity_values_are_valid(self):
        for value, _ in Rarity.choices:
            card = make_card(rarity=value)
            self.assertEqual(card.rarity, value)

    def test_rarity_stored_as_string_key(self):
        card = make_card(rarity=Rarity.EPIC)
        self.assertEqual(card.rarity, 'epic')

    def test_get_rarity_display(self):
        card = make_card(rarity=Rarity.ULTRA_RARE)
        self.assertEqual(card.get_rarity_display(), 'Ultra Rare')

    # Stats
    def test_stats_dict_has_exactly_six_keys(self):
        card = make_card()
        self.assertEqual(
            set(card.stats.keys()),
            {'finishing', 'defending', 'sprinting', 'strength', 'tech', 'leadership'},
        )

    def test_stats_values_match_fields(self):
        card = make_card(
            finishing=80, defending=70, sprinting=60,
            strength=50, tech=40, leadership=30,
        )
        self.assertEqual(card.stats['finishing'], 80)
        self.assertEqual(card.stats['leadership'], 30)

    def test_overall_is_rounded_average_of_six_stats(self):
        card = make_card(
            finishing=60, defending=60, sprinting=60,
            strength=60, tech=60, leadership=60,
        )
        self.assertEqual(card.overall, 60)

    def test_overall_rounds_correctly(self):
        # (99+99+99+99+99+0) / 6 = 82.5 → Python banker's rounding → 82
        card = make_card(
            finishing=99, defending=99, sprinting=99,
            strength=99, tech=99, leadership=0,
        )
        self.assertEqual(card.overall, 82)

    def test_overall_all_zeros(self):
        card = make_card(
            finishing=0, defending=0, sprinting=0,
            strength=0, tech=0, leadership=0,
        )
        self.assertEqual(card.overall, 0)

    def test_overall_all_max(self):
        card = make_card(
            finishing=99, defending=99, sprinting=99,
            strength=99, tech=99, leadership=99,
        )
        self.assertEqual(card.overall, 99)

    # image_url optional
    def test_image_url_blank_by_default(self):
        card = make_card()
        self.assertEqual(card.image_url, '')

    def test_image_url_can_be_set(self):
        card = make_card(image_url='https://example.com/card.png')
        self.assertEqual(card.image_url, 'https://example.com/card.png')


# ──────────────────────────────────────────────────────────────────────────────
# CollectionItem model
# ──────────────────────────────────────────────────────────────────────────────

class CollectionItemModelTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.card = make_card(player_name='Ronaldo', rarity=Rarity.RARE)

    # add_to_collection
    def test_add_to_collection_creates_item(self):
        item, created = CollectionItem.add_to_collection(self.user, self.card)
        self.assertTrue(created)
        self.assertEqual(item.quantity, 1)

    def test_add_to_collection_sets_date_obtained(self):
        item, _ = CollectionItem.add_to_collection(self.user, self.card)
        self.assertIsNotNone(item.date_obtained)

    def test_add_duplicate_increments_quantity(self):
        CollectionItem.add_to_collection(self.user, self.card)
        item, created = CollectionItem.add_to_collection(self.user, self.card)
        self.assertFalse(created)
        self.assertEqual(item.quantity, 2)

    def test_add_three_times_quantity_is_three(self):
        for _ in range(3):
            CollectionItem.add_to_collection(self.user, self.card)
        item = CollectionItem.objects.get(user=self.user, card=self.card)
        self.assertEqual(item.quantity, 3)

    def test_only_one_record_created_for_duplicates(self):
        for _ in range(5):
            CollectionItem.add_to_collection(self.user, self.card)
        self.assertEqual(
            CollectionItem.objects.filter(user=self.user, card=self.card).count(), 1
        )

    def test_different_users_each_get_own_record(self):
        user2 = make_user(email='other@example.com')
        CollectionItem.add_to_collection(self.user, self.card)
        CollectionItem.add_to_collection(user2, self.card)
        self.assertEqual(CollectionItem.objects.filter(card=self.card).count(), 2)

    def test_different_cards_each_get_own_record(self):
        card2 = make_card(player_name='Messi')
        CollectionItem.add_to_collection(self.user, self.card)
        CollectionItem.add_to_collection(self.user, card2)
        self.assertEqual(CollectionItem.objects.filter(user=self.user).count(), 2)

    def test_str_contains_user_email(self):
        item, _ = CollectionItem.add_to_collection(self.user, self.card)
        self.assertIn(self.user.email, str(item))

    def test_str_contains_player_name(self):
        item, _ = CollectionItem.add_to_collection(self.user, self.card)
        self.assertIn('Ronaldo', str(item))

    def test_str_contains_quantity(self):
        CollectionItem.add_to_collection(self.user, self.card)
        item, _ = CollectionItem.add_to_collection(self.user, self.card)
        self.assertIn('x2', str(item))

    # Cascade deletes
    def test_item_deleted_when_user_deleted(self):
        item, _ = CollectionItem.add_to_collection(self.user, self.card)
        item_pk = item.pk
        self.user.delete()
        self.assertFalse(CollectionItem.objects.filter(pk=item_pk).exists())

    def test_item_deleted_when_card_deleted(self):
        item, _ = CollectionItem.add_to_collection(self.user, self.card)
        item_pk = item.pk
        self.card.delete()
        self.assertFalse(CollectionItem.objects.filter(pk=item_pk).exists())


# ──────────────────────────────────────────────────────────────────────────────
# CollectionView — rarity selector page (/cards/)
# ──────────────────────────────────────────────────────────────────────────────

class CollectionViewTests(TestCase):

    URL = '/cards/'

    def setUp(self):
        self.user = make_user()

    def test_requires_login(self):
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 302)

    def test_redirects_unauthenticated_to_landing(self):
        response = self.client.get(self.URL)
        self.assertIn('/', response['Location'])

    def test_returns_200_when_logged_in(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_context_contains_rarities(self):
        self.client.force_login(self.user)
        response = self.client.get(self.URL)
        self.assertIn('rarities', response.context)

    def test_five_rarity_entries_returned(self):
        self.client.force_login(self.user)
        response = self.client.get(self.URL)
        self.assertEqual(len(response.context['rarities']), 5)

    def test_owned_count_is_zero_with_no_cards(self):
        self.client.force_login(self.user)
        response = self.client.get(self.URL)
        for rarity in response.context['rarities']:
            self.assertEqual(rarity['owned'], 0)

    def test_owned_count_reflects_collection(self):
        card = make_card(rarity=Rarity.COMMON)
        CollectionItem.add_to_collection(self.user, card)
        self.client.force_login(self.user)
        response = self.client.get(self.URL)
        common = next(r for r in response.context['rarities'] if r['key'] == Rarity.COMMON)
        self.assertEqual(common['owned'], 1)

    def test_owned_count_includes_quantity(self):
        card = make_card(rarity=Rarity.RARE)
        CollectionItem.add_to_collection(self.user, card)
        CollectionItem.add_to_collection(self.user, card)
        self.client.force_login(self.user)
        response = self.client.get(self.URL)
        rare = next(r for r in response.context['rarities'] if r['key'] == Rarity.RARE)
        self.assertEqual(rare['owned'], 2)

    def test_total_count_reflects_catalogue(self):
        make_card(rarity=Rarity.LEGENDARY)
        make_card(rarity=Rarity.LEGENDARY)
        self.client.force_login(self.user)
        response = self.client.get(self.URL)
        legendary = next(
            r for r in response.context['rarities'] if r['key'] == Rarity.LEGENDARY
        )
        self.assertEqual(legendary['total'], 2)

    def test_other_users_collection_not_counted(self):
        other = make_user(email='other@example.com')
        card = make_card(rarity=Rarity.EPIC)
        CollectionItem.add_to_collection(other, card)
        self.client.force_login(self.user)
        response = self.client.get(self.URL)
        epic = next(r for r in response.context['rarities'] if r['key'] == Rarity.EPIC)
        self.assertEqual(epic['owned'], 0)


# ──────────────────────────────────────────────────────────────────────────────
# RarityDetailView — per-rarity card list (/cards/<rarity>/)
# ──────────────────────────────────────────────────────────────────────────────

class RarityDetailViewTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.card = make_card(player_name='Mbappe', rarity=Rarity.RARE)

    def _url(self, rarity=Rarity.RARE):
        return f'/cards/{rarity}/'

    def test_requires_login(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_returns_200_for_valid_rarity(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_returns_404_for_invalid_rarity(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/cards/nonexistent/').status_code, 404)

    def test_all_valid_rarities_return_200(self):
        self.client.force_login(self.user)
        for value, _ in Rarity.choices:
            response = self.client.get(f'/cards/{value}/')
            self.assertEqual(response.status_code, 200, f'Failed for rarity: {value}')

    def test_context_contains_cards(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        self.assertIn('cards', response.context)

    def test_only_cards_of_correct_rarity_returned(self):
        make_card(player_name='Messi', rarity=Rarity.LEGENDARY)
        self.client.force_login(self.user)
        response = self.client.get(self._url(Rarity.RARE))
        names = [e['card'].player_name for e in response.context['cards']]
        self.assertIn('Mbappe', names)
        self.assertNotIn('Messi', names)

    def test_unowned_card_has_quantity_zero(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        entry = response.context['cards'][0]
        self.assertEqual(entry['quantity'], 0)
        self.assertFalse(entry['owned'])

    def test_owned_card_has_correct_quantity(self):
        CollectionItem.add_to_collection(self.user, self.card)
        CollectionItem.add_to_collection(self.user, self.card)
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        entry = response.context['cards'][0]
        self.assertEqual(entry['quantity'], 2)
        self.assertTrue(entry['owned'])

    def test_context_contains_rarity_label(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        self.assertIn('rarity_label', response.context)
        self.assertEqual(response.context['rarity_label'], 'Rare')

    def test_context_contains_rarity_meta(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        self.assertIn('rarity_meta', response.context)

    def test_empty_rarity_returns_empty_card_list(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url(Rarity.LEGENDARY))
        self.assertEqual(len(response.context['cards']), 0)

    def test_other_users_ownership_not_shown(self):
        other = make_user(email='other@example.com')
        CollectionItem.add_to_collection(other, self.card)
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        entry = response.context['cards'][0]
        self.assertFalse(entry['owned'])
