"""
Core game logic for Football Trumps.
"""

import random

from cards.models import Card, Rarity

ATTRIBUTES = ['finishing', 'defending', 'sprinting', 'strength', 'tech', 'leadership']

ATTR_LABELS = {
    'finishing':  'FIN',
    'defending':  'DEF',
    'sprinting':  'SPR',
    'strength':   'STR',
    'tech':       'TEC',
    'leadership': 'LDR',
}

def _bot_deck(user_card_ids):
    """
    Build a 15-card bot deck that mirrors the rarity distribution of the
    user's selected deck, so both sides have equally matched cards.
    """
    from collections import Counter

    user_cards = list(Card.objects.filter(card_id__in=user_card_ids))
    rarity_counts = Counter(c.rarity for c in user_cards)

    # Pool of all cards grouped by rarity
    pool = {}
    for rarity, _ in rarity_counts.items():
        pool[rarity] = list(Card.objects.filter(rarity=rarity))
        random.shuffle(pool[rarity])

    chosen = []
    seen = set()

    # Pick the same number per rarity as the user has
    for rarity, count in rarity_counts.items():
        candidates = [c for c in pool[rarity] if c.card_id not in seen]
        picks = candidates[:count]
        chosen.extend(picks)
        seen.update(c.card_id for c in picks)

    # Fallback: if a rarity bucket didn't have enough cards, fill from any rarity
    if len(chosen) < 15:
        all_remaining = list(
            Card.objects.exclude(card_id__in=seen).order_by('?')[:15 - len(chosen)]
        )
        chosen.extend(all_remaining)

    random.shuffle(chosen)
    return [str(c.card_id) for c in chosen[:15]]


def create_game(user):
    """Create a new GameSession for the user, cancelling any active one."""
    from .models import GameSession

    GameSession.objects.filter(user=user, status=GameSession.STATUS_ACTIVE).update(
        status=GameSession.STATUS_ABANDONED
    )

    user_card_ids = [str(cid) for cid in user.active_deck.card_ids]
    random.shuffle(user_card_ids)

    first_turn = random.choice([GameSession.TURN_USER, GameSession.TURN_BOT])

    return GameSession.objects.create(
        user=user,
        status=GameSession.STATUS_ACTIVE,
        user_deck=user_card_ids,
        bot_deck=_bot_deck(user_card_ids),
        current_turn=first_turn,
        round_number=0,
    )


def process_turn(session, attribute, picker):
    """
    Resolve one round of the game.

    attribute — one of ATTRIBUTES
    picker    — 'user' or 'bot' (who chose the attribute)
    """
    user_card = Card.objects.get(card_id=session.user_deck[0])
    bot_card  = Card.objects.get(card_id=session.bot_deck[0])

    user_val = getattr(user_card, attribute)
    bot_val  = getattr(bot_card,  attribute)

    # Ties go to the picker
    if user_val > bot_val or (user_val == bot_val and picker == 'user'):
        winner = 'user'
    else:
        winner = 'bot'

    user_deck = list(session.user_deck[1:])
    bot_deck  = list(session.bot_deck[1:])

    if winner == 'user':
        # Winner gets both cards: their own first, then opponent's
        user_deck += [str(user_card.card_id), str(bot_card.card_id)]
        next_turn = 'user'
    else:
        bot_deck += [str(bot_card.card_id), str(user_card.card_id)]
        next_turn = 'bot'

    # Check game over
    if len(user_deck) == 0:
        status = 'lost'
    elif len(bot_deck) == 0:
        status = 'won'
    else:
        status = 'active'

    session.user_deck    = user_deck
    session.bot_deck     = bot_deck
    session.current_turn = next_turn
    session.round_number += 1
    session.status       = status
    session.last_result  = {
        'attribute':       attribute,
        'attribute_label': ATTR_LABELS[attribute],
        'user_card_id':    str(user_card.card_id),
        'bot_card_id':     str(bot_card.card_id),
        'user_val':        user_val,
        'bot_val':         bot_val,
        'winner':          winner,
        'picker':          picker,
    }
    session.save()
    return session


def bot_pick_attribute(card):
    """Bot always picks the attribute where it has the highest value."""
    return max(ATTRIBUTES, key=lambda a: getattr(card, a))
