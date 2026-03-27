from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .models import Card, CollectionItem, Rarity

RARITY_META = [
    {
        'key': Rarity.COMMON,
        'label': 'Common',
        'css_class': 'card-common',
        'stars': 2,
    },
    {
        'key': Rarity.RARE,
        'label': 'Rare',
        'css_class': 'card-rare',
        'stars': 3,
    },
    {
        'key': Rarity.ULTRA_RARE,
        'label': 'Ultra Rare',
        'css_class': 'card-ultra-rare',
        'stars': 4,
    },
    {
        'key': Rarity.LEGENDARY,
        'label': 'Legendary',
        'css_class': 'card-legendary',
        'stars': 5,
    },
    {
        'key': Rarity.EPIC,
        'label': 'Epic',
        'css_class': 'card-epic',
        'stars': 5,
    },
]


@method_decorator(login_required, name='dispatch')
class CollectionView(View):
    """Landing page — shows the five rarity category cards to select from."""

    template_name = 'cards/collection.html'

    def get(self, request):
        # Count how many cards the user owns per rarity
        owned_counts = {}
        for item in CollectionItem.objects.filter(user=request.user).select_related('card'):
            rarity = item.card.rarity
            owned_counts[rarity] = owned_counts.get(rarity, 0) + item.quantity

        rarities = []
        for meta in RARITY_META:
            total_in_rarity = Card.objects.filter(rarity=meta['key']).count()
            rarities.append({
                **meta,
                'owned': owned_counts.get(meta['key'], 0),
                'total': total_in_rarity,
            })

        return render(request, self.template_name, {'rarities': rarities})


@method_decorator(login_required, name='dispatch')
class RarityDetailView(View):
    """Shows all cards of a given rarity, highlighting ones the user owns."""

    template_name = 'cards/rarity_detail.html'

    def get(self, request, rarity):
        if rarity not in Rarity.values:
            from django.http import Http404
            raise Http404

        all_cards = Card.objects.filter(rarity=rarity).order_by('player_name')
        owned_map = {
            item.card_id: item.quantity
            for item in CollectionItem.objects.filter(user=request.user, card__rarity=rarity)
        }

        cards = [
            {
                'card': card,
                'quantity': owned_map.get(card.card_id, 0),
                'owned': card.card_id in owned_map,
            }
            for card in all_cards
        ]

        rarity_meta = next(m for m in RARITY_META if m['key'] == rarity)

        return render(request, self.template_name, {
            'cards': cards,
            'rarity_meta': rarity_meta,
            'rarity_label': dict(Rarity.choices)[rarity],
        })
