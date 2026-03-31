from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .pack_logic import PACK_CONFIG, open_pack


@method_decorator(login_required, name='dispatch')
class StoreView(View):
    template_name = 'store/store.html'

    def get(self, request):
        packs = [
            {'type': 'bronze',  **PACK_CONFIG['bronze']},
            {'type': 'silver',  **PACK_CONFIG['silver']},
            {'type': 'gold',    **PACK_CONFIG['gold']},
            {'type': 'premium', **PACK_CONFIG['premium']},
        ]
        return render(request, self.template_name, {
            'packs': packs,
            'points': request.user.settings.points,
        })


@method_decorator(login_required, name='dispatch')
class PackOpenView(View):
    template_name = 'store/pack_result.html'

    def post(self, request, pack_type):
        if pack_type not in PACK_CONFIG:
            return redirect('store:store')

        config = PACK_CONFIG[pack_type]
        settings = request.user.settings

        if settings.points < config['cost']:
            return redirect('store:store')

        # Deduct points then open
        settings.points -= config['cost']
        settings.save(update_fields=['points'])

        results = open_pack(pack_type, request.user)

        new_count = sum(1 for r in results if r['added'])
        dup_count = len(results) - new_count

        return render(request, self.template_name, {
            'pack_type': pack_type,
            'pack_label': config['label'],
            'results': results,
            'new_count': new_count,
            'dup_count': dup_count,
            'points': settings.points,
        })

    def get(self, request, pack_type):
        return redirect('store:store')
