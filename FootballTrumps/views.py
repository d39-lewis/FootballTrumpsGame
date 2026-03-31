from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View


class LandingView(View):
    """Landing page — always shows the login/sign up prompt."""
    def get(self, request):
        return render(request, 'landing.html')


@method_decorator(login_required, name='dispatch')
class HowToPlayView(View):
    def get(self, request):
        return render(request, 'how_to_play.html')


@method_decorator(login_required, name='dispatch')
class HomeView(View):
    def get(self, request):
        context = {
            'wins': 0,
            'losses': 0,
            'points': request.user.settings.points,
        }
        return render(request, 'home.html', context)
