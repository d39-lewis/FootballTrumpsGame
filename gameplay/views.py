from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from cards.models import Card, CollectionItem

from .game_logic import ATTR_LABELS, ATTRIBUTES, bot_pick_attribute, create_game, process_turn
from .models import ActiveDeck, GameSession


def _get_active_session(user):
    return GameSession.objects.filter(user=user, status=GameSession.STATUS_ACTIVE).first()


def _deck_ready(user):
    try:
        return user.active_deck.is_ready
    except ActiveDeck.DoesNotExist:
        return False


# ── Deck selection ────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class DeckView(View):
    template_name = 'gameplay/deck.html'

    def get(self, request):
        owned = (
            CollectionItem.objects
            .filter(user=request.user)
            .select_related('card')
            .order_by('card__rarity', 'card__player_name')
        )

        try:
            selected_ids = set(str(cid) for cid in request.user.active_deck.card_ids)
        except ActiveDeck.DoesNotExist:
            selected_ids = set()

        cards = [
            {'card': item.card, 'selected': str(item.card.card_id) in selected_ids}
            for item in owned
        ]

        return render(request, self.template_name, {
            'cards': cards,
            'selected_count': len(selected_ids),
            'total_owned': len(cards),
            'error': request.GET.get('error'),
        })

    def post(self, request):
        card_ids = request.POST.getlist('card_ids')

        if len(card_ids) != 15:
            return redirect('/gameplay/deck/?error=Select exactly 15 cards.')

        owned_ids = set(
            str(cid) for cid in
            CollectionItem.objects.filter(user=request.user).values_list('card_id', flat=True)
        )
        if not all(cid in owned_ids for cid in card_ids):
            return redirect('/gameplay/deck/?error=Invalid selection.')

        deck, _ = ActiveDeck.objects.get_or_create(user=request.user)
        deck.card_ids = card_ids
        deck.save()

        return redirect('gameplay:play')


# ── Game ──────────────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class PlayView(View):
    template_name = 'gameplay/play.html'

    def get(self, request):
        if not _deck_ready(request.user):
            return redirect('gameplay:deck')

        session = _get_active_session(request.user)
        if not session:
            session = create_game(request.user)

        return self._render(request, session)

    def _render(self, request, session):
        user_top = Card.objects.get(card_id=session.user_deck[0]) if session.user_deck else None
        bot_top  = Card.objects.get(card_id=session.bot_deck[0])  if session.bot_deck  else None

        last_result = None
        if session.last_result:
            lr = session.last_result
            last_result = {
                **lr,
                'user_card': Card.objects.get(card_id=lr['user_card_id']),
                'bot_card':  Card.objects.get(card_id=lr['bot_card_id']),
            }

        return render(request, self.template_name, {
            'session':     session,
            'user_top':    user_top,
            'bot_top':     bot_top,
            'last_result': last_result,
            'attributes':  ATTRIBUTES,
            'attr_labels': ATTR_LABELS,
        })

    def post(self, request):
        if not _deck_ready(request.user):
            return redirect('gameplay:deck')

        session = _get_active_session(request.user)
        if not session:
            return redirect('gameplay:play')

        action = request.POST.get('action')

        if action == 'pick' and session.current_turn == GameSession.TURN_USER:
            attribute = request.POST.get('attribute')
            if attribute in ATTRIBUTES:
                process_turn(session, attribute, picker='user')
                session.refresh_from_db()

        elif action == 'bot_play' and session.current_turn == GameSession.TURN_BOT:
            bot_card = Card.objects.get(card_id=session.bot_deck[0])
            attribute = bot_pick_attribute(bot_card)
            process_turn(session, attribute, picker='bot')
            session.refresh_from_db()

        elif action == 'new_game':
            session.status = GameSession.STATUS_ABANDONED
            session.save()
            return redirect('gameplay:deck')

        if session.status in (GameSession.STATUS_WON, GameSession.STATUS_LOST):
            if session.status == GameSession.STATUS_WON:
                request.user.settings.points += 100
                request.user.settings.save(update_fields=['points'])
            return redirect('gameplay:result', pk=session.pk)

        return redirect('gameplay:play')


# ── Result ────────────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class ResultView(View):
    template_name = 'gameplay/result.html'

    def get(self, request, pk):
        session = get_object_or_404(
            GameSession, pk=pk, user=request.user
        )
        if session.status == GameSession.STATUS_ACTIVE:
            return redirect('gameplay:play')

        return render(request, self.template_name, {
            'session': session,
            'won': session.status == GameSession.STATUS_WON,
        })
