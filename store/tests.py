"""
Tests for the store app — pack logic, store view, and pack opening view.
"""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from cards.models import Card, CollectionItem, Rarity
from store.pack_logic import PACK_CONFIG, _pick_rarity, open_pack


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_user(email='buyer@example.com', password='Pass1234!'):
    return User.objects.create_user(email=email, password=password)


def make_card(name='Test Player', rarity=Rarity.COMMON, **kwargs):
    defaults = dict(
        finishing=70, defending=70, sprinting=70,
        strength=70, tech=70, leadership=70,
    )
    defaults.update(kwargs)
    return Card.objects.create(player_name=name, rarity=rarity, **defaults)


# ── Pack config ───────────────────────────────────────────────────────────────

class PackConfigTests(TestCase):

    def test_all_four_packs_defined(self):
        self.assertEqual(set(PACK_CONFIG.keys()), {'bronze', 'silver', 'gold', 'premium'})

    def test_each_pack_has_cost(self):
        for key, cfg in PACK_CONFIG.items():
            self.assertIn('cost', cfg, f'{key} missing cost')

    def test_each_pack_has_card_count(self):
        for key, cfg in PACK_CONFIG.items():
            self.assertGreater(cfg['cards'], 0, f'{key} card count must be > 0')

    def test_probabilities_sum_to_one(self):
        rarity_keys = ['common', 'rare', 'ultra_rare', 'legendary', 'epic']
        for key, cfg in PACK_CONFIG.items():
            total = sum(cfg[r] for r in rarity_keys)
            self.assertAlmostEqual(total, 1.0, places=5, msg=f'{key} probs do not sum to 1')

    def test_bronze_has_15_cards(self):
        self.assertEqual(PACK_CONFIG['bronze']['cards'], 15)

    def test_silver_gold_premium_have_5_cards(self):
        for key in ('silver', 'gold', 'premium'):
            self.assertEqual(PACK_CONFIG[key]['cards'], 5)


# ── Pick rarity ───────────────────────────────────────────────────────────────

class PickRarityTests(TestCase):

    def test_returns_a_valid_rarity_key(self):
        valid = {'common', 'rare', 'ultra_rare', 'legendary', 'epic'}
        for _ in range(50):
            result = _pick_rarity(PACK_CONFIG['bronze'])
            self.assertIn(result, valid)

    def test_bronze_never_returns_legendary_or_epic(self):
        """Bronze probabilities for legendary and epic are 0.00."""
        for _ in range(200):
            result = _pick_rarity(PACK_CONFIG['bronze'])
            self.assertNotIn(result, ('legendary', 'epic'))


# ── open_pack logic ───────────────────────────────────────────────────────────

class OpenPackTests(TestCase):

    def setUp(self):
        self.user = make_user()
        # Seed enough cards across rarities
        for i in range(20):
            make_card(name=f'Common {i}', rarity=Rarity.COMMON)
        for i in range(5):
            make_card(name=f'Rare {i}', rarity=Rarity.RARE)

    def test_bronze_returns_15_results(self):
        results = open_pack('bronze', self.user)
        self.assertEqual(len(results), 15)

    def test_no_duplicate_cards_within_pack(self):
        results = open_pack('bronze', self.user)
        card_ids = [r['card'].card_id for r in results]
        self.assertEqual(len(card_ids), len(set(card_ids)))

    def test_each_result_has_required_keys(self):
        results = open_pack('silver', self.user)
        for r in results:
            self.assertIn('card', r)
            self.assertIn('added', r)
            self.assertIn('rarity_label', r)

    def test_new_cards_added_to_collection(self):
        results = open_pack('bronze', self.user)
        added_ids = {r['card'].card_id for r in results if r['added']}
        owned_ids = set(
            CollectionItem.objects.filter(user=self.user).values_list('card_id', flat=True)
        )
        self.assertTrue(added_ids.issubset(owned_ids))

    def test_already_owned_card_not_added_again(self):
        card = make_card(name='Owned Card', rarity=Rarity.COMMON)
        CollectionItem.add_to_collection(self.user, card)
        qty_before = CollectionItem.objects.get(user=self.user, card=card).quantity

        # Force that specific card to be picked first
        with patch('store.pack_logic.random.choice', return_value=card):
            with patch('store.pack_logic._pick_rarity', return_value='common'):
                results = open_pack('bronze', self.user)

        # The card appears in results but marked not added
        owned_results = [r for r in results if r['card'].card_id == card.card_id]
        self.assertTrue(len(owned_results) >= 1)
        self.assertFalse(owned_results[0]['added'])

        # Quantity unchanged
        qty_after = CollectionItem.objects.get(user=self.user, card=card).quantity
        self.assertEqual(qty_before, qty_after)


# ── StoreView ─────────────────────────────────────────────────────────────────

class StoreViewTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.url = reverse('store:store')

    def test_redirects_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_returns_200_when_logged_in(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_contains_four_packs(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['packs']), 4)

    def test_context_contains_points(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context['points'], 500)

    def test_pack_types_present(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        types = [p['type'] for p in response.context['packs']]
        self.assertEqual(types, ['bronze', 'silver', 'gold', 'premium'])


# ── PackOpenView ──────────────────────────────────────────────────────────────

class PackOpenViewTests(TestCase):

    def setUp(self):
        self.user = make_user()
        # Seed 20 common cards so bronze pack can fill 15 slots
        for i in range(20):
            make_card(name=f'Common {i}', rarity=Rarity.COMMON)

    def _url(self, pack_type):
        return reverse('store:open_pack', args=[pack_type])

    def test_get_redirects_to_store(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url('bronze'))
        self.assertRedirects(response, reverse('store:store'))

    def test_redirects_unauthenticated(self):
        response = self.client.post(self._url('bronze'))
        self.assertEqual(response.status_code, 302)

    def test_invalid_pack_type_redirects(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url('diamond'))
        self.assertRedirects(response, reverse('store:store'))

    def test_insufficient_points_redirects(self):
        self.user.settings.points = 100  # bronze costs 500
        self.user.settings.save()
        self.client.force_login(self.user)
        response = self.client.post(self._url('bronze'))
        self.assertRedirects(response, reverse('store:store'))

    def test_points_not_deducted_when_insufficient(self):
        self.user.settings.points = 100
        self.user.settings.save()
        self.client.force_login(self.user)
        self.client.post(self._url('bronze'))
        self.user.settings.refresh_from_db()
        self.assertEqual(self.user.settings.points, 100)

    def test_successful_purchase_deducts_points(self):
        self.client.force_login(self.user)
        self.client.post(self._url('bronze'))
        self.user.settings.refresh_from_db()
        self.assertEqual(self.user.settings.points, 500 - PACK_CONFIG['bronze']['cost'])

    def test_successful_purchase_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url('bronze'))
        self.assertEqual(response.status_code, 200)

    def test_result_context_has_results(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url('bronze'))
        self.assertIn('results', response.context)

    def test_result_context_has_correct_counts(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url('bronze'))
        ctx = response.context
        self.assertEqual(ctx['new_count'] + ctx['dup_count'], len(ctx['results']))

    def test_result_context_has_remaining_points(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url('bronze'))
        expected = 500 - PACK_CONFIG['bronze']['cost']
        self.assertEqual(response.context['points'], expected)

    def test_cards_added_to_collection(self):
        self.client.force_login(self.user)
        self.client.post(self._url('bronze'))
        count = CollectionItem.objects.filter(user=self.user).count()
        self.assertGreater(count, 0)
