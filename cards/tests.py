from django.test import TestCase

from accounts.models import User
from cards.models import Card, CollectionItem, Rarity


def make_card(**kwargs):
    defaults = dict(
        player_name='Test Player',
        rarity=Rarity.COMMON,
        finishing=50, defending=50, sprinting=50,
        strength=50, tech=50, leadership=50,
    )
    defaults.update(kwargs)
    return Card.objects.create(**defaults)


class CardModelTests(TestCase):
    def test_str(self):
        card = make_card(player_name='Messi', rarity=Rarity.LEGENDARY)
        self.assertEqual(str(card), 'Messi (Legendary)')

    def test_overall_is_average_of_six_stats(self):
        card = make_card(finishing=60, defending=60, sprinting=60,
                         strength=60, tech=60, leadership=60)
        self.assertEqual(card.overall, 60)

    def test_stats_dict_has_six_keys(self):
        card = make_card()
        self.assertEqual(set(card.stats.keys()),
                         {'finishing', 'defending', 'sprinting', 'strength', 'tech', 'leadership'})

    def test_rarity_choices_constrained(self):
        card = make_card(rarity=Rarity.EPIC)
        self.assertEqual(card.rarity, 'epic')


class CollectionItemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='collector@example.com', password='pass')
        self.card = make_card(player_name='Ronaldo', rarity=Rarity.RARE)

    def test_add_to_collection_creates_item(self):
        item, created = CollectionItem.add_to_collection(self.user, self.card)
        self.assertTrue(created)
        self.assertEqual(item.quantity, 1)

    def test_add_duplicate_increments_quantity(self):
        CollectionItem.add_to_collection(self.user, self.card)
        item, created = CollectionItem.add_to_collection(self.user, self.card)
        self.assertFalse(created)
        self.assertEqual(item.quantity, 2)

    def test_unique_per_user_and_card(self):
        CollectionItem.add_to_collection(self.user, self.card)
        self.assertEqual(CollectionItem.objects.filter(user=self.user, card=self.card).count(), 1)

    def test_str(self):
        item, _ = CollectionItem.add_to_collection(self.user, self.card)
        self.assertIn('collector@example.com', str(item))
        self.assertIn('Ronaldo', str(item))


class CollectionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='view@example.com', password='pass')
        self.card = make_card()

    def test_collection_requires_login(self):
        response = self.client.get('/cards/')
        self.assertEqual(response.status_code, 302)

    def test_collection_loads_for_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get('/cards/')
        self.assertEqual(response.status_code, 200)
