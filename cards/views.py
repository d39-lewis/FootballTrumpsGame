from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .forms import CardForm
from .models import Card, CollectionItem, Rarity

# ── Rarity metadata used across views ────────────────────────────────────────

RARITY_META = [
    {'key': Rarity.COMMON,     'label': 'Common',     'css_class': 'card-common',     'stars': 2},
    {'key': Rarity.RARE,       'label': 'Rare',       'css_class': 'card-rare',       'stars': 3},
    {'key': Rarity.ULTRA_RARE, 'label': 'Ultra Rare', 'css_class': 'card-ultra-rare', 'stars': 4},
    {'key': Rarity.LEGENDARY,  'label': 'Legendary',  'css_class': 'card-legendary',  'stars': 5},
    {'key': Rarity.EPIC,       'label': 'Epic',       'css_class': 'card-epic',       'stars': 5},
]

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url='landing')


# ── Player-facing views ───────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class CollectionView(View):
    """Landing page — shows the five rarity category cards to select from."""
    template_name = 'cards/collection.html'

    def get(self, request):
        owned_counts = {}
        for item in CollectionItem.objects.filter(user=request.user).select_related('card'):
            rarity = item.card.rarity
            owned_counts[rarity] = owned_counts.get(rarity, 0) + item.quantity

        rarities = []
        for meta in RARITY_META:
            total = Card.objects.filter(rarity=meta['key']).count()
            rarities.append({**meta, 'owned': owned_counts.get(meta['key'], 0), 'total': total})

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
            {'card': card, 'quantity': owned_map.get(card.card_id, 0),
             'owned': card.card_id in owned_map}
            for card in all_cards
        ]

        rarity_meta = next(m for m in RARITY_META if m['key'] == rarity)
        return render(request, self.template_name, {
            'cards': cards,
            'rarity_meta': rarity_meta,
            'rarity_label': dict(Rarity.choices)[rarity],
        })


# ── Staff card management views ───────────────────────────────────────────────

@method_decorator([login_required, staff_required], name='dispatch')
class CardManageListView(View):
    """Staff-only: list all cards grouped by rarity."""
    template_name = 'cards/manage_list.html'

    def get(self, request):
        grouped = {meta['label']: {'meta': meta, 'cards': []} for meta in RARITY_META}
        for card in Card.objects.all().order_by('rarity', 'player_name'):
            label = card.get_rarity_display()
            if label in grouped:
                grouped[label]['cards'].append(card)

        return render(request, self.template_name, {
            'grouped': grouped,
            'rarity_order': [m['label'] for m in RARITY_META],
            'total': Card.objects.count(),
        })


@method_decorator([login_required, staff_required], name='dispatch')
class CardCreateView(View):
    """Staff-only: add a new card."""
    template_name = 'cards/manage_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': CardForm(), 'action': 'Add'})

    def post(self, request):
        form = CardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cards:manage_list')
        return render(request, self.template_name, {'form': form, 'action': 'Add'})


@method_decorator([login_required, staff_required], name='dispatch')
class CardUpdateView(View):
    """Staff-only: edit an existing card."""
    template_name = 'cards/manage_form.html'

    def get(self, request, card_id):
        card = get_object_or_404(Card, card_id=card_id)
        return render(request, self.template_name,
                      {'form': CardForm(instance=card), 'card': card, 'action': 'Edit'})

    def post(self, request, card_id):
        card = get_object_or_404(Card, card_id=card_id)
        form = CardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            return redirect('cards:manage_list')
        return render(request, self.template_name,
                      {'form': form, 'card': card, 'action': 'Edit'})


@method_decorator([login_required, staff_required], name='dispatch')
class CardDeleteView(View):
    """Staff-only: delete a card (POST only)."""

    def post(self, request, card_id):
        card = get_object_or_404(Card, card_id=card_id)
        card.delete()
        return redirect('cards:manage_list')
