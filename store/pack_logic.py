"""
Pack opening logic for the store.
"""

import random

from cards.models import Card, CollectionItem, Rarity

PACK_CONFIG = {
    "bronze": {
        "label": "Bronze Pack",
        "cost": 500,
        "cards": 15,
        "no_duplicates_in_pack": True,
        "common":     0.92,
        "rare":       0.07,
        "ultra_rare": 0.01,
        "legendary":  0.00,
        "epic":       0.00,
    },
    "silver": {
        "label": "Silver Pack",
        "cost": 750,
        "cards": 5,
        "no_duplicates_in_pack": False,
        "common":     0.65,
        "rare":       0.25,
        "ultra_rare": 0.07,
        "legendary":  0.005,
        "epic":       0.025,
    },
    "gold": {
        "label": "Gold Pack",
        "cost": 1000,
        "cards": 5,
        "no_duplicates_in_pack": False,
        "common":     0.45,
        "rare":       0.30,
        "ultra_rare": 0.15,
        "legendary":  0.02,
        "epic":       0.08,
    },
    "premium": {
        "label": "Premium Pack",
        "cost": 1500,
        "cards": 5,
        "no_duplicates_in_pack": False,
        "common":     0.25,
        "rare":       0.30,
        "ultra_rare": 0.22,
        "legendary":  0.08,
        "epic":       0.15,
    },
}

_RARITY_KEYS = ["common", "rare", "ultra_rare", "legendary", "epic"]

_RARITY_DB_MAP = {
    "common":     Rarity.COMMON,
    "rare":       Rarity.RARE,
    "ultra_rare": Rarity.ULTRA_RARE,
    "legendary":  Rarity.LEGENDARY,
    "epic":       Rarity.EPIC,
}


def _pick_rarity(config):
    """Weighted random rarity selection."""
    roll = random.random()
    cumulative = 0.0
    for key in _RARITY_KEYS:
        cumulative += config.get(key, 0)
        if roll < cumulative:
            return key
    return "common"


def open_pack(pack_type, user):
    """
    Open a pack for a user.

    Returns a list of dicts:
        {
            'card':          Card instance,
            'added':         bool  — True if added to collection, False if already owned,
            'rarity_label':  str   — display label for rarity,
        }

    Points are NOT deducted here — the view handles that before calling this.
    """
    config = PACK_CONFIG[pack_type]
    n_cards = config["cards"]
    used_ids = set()
    results = []

    # Pre-load owned card IDs for this user to avoid per-card queries
    owned_ids = set(
        CollectionItem.objects.filter(user=user).values_list("card_id", flat=True)
    )

    for _ in range(n_cards):
        rarity_key = _pick_rarity(config)
        rarity_value = _RARITY_DB_MAP[rarity_key]

        # Exclude cards already chosen in this pack (no duplicates within pack)
        qs = Card.objects.filter(rarity=rarity_value).exclude(card_id__in=used_ids)

        # Fallback: if this rarity is empty, try common
        if not qs.exists():
            qs = Card.objects.filter(rarity=Rarity.COMMON).exclude(card_id__in=used_ids)

        if not qs.exists():
            continue  # All cards exhausted — skip slot

        card = random.choice(list(qs))
        used_ids.add(card.card_id)

        already_owned = card.card_id in owned_ids
        if not already_owned:
            CollectionItem.add_to_collection(user, card)
            owned_ids.add(card.card_id)

        results.append({
            "card": card,
            "added": not already_owned,
            "rarity_label": dict(Rarity.choices)[rarity_value],
        })

    return results
