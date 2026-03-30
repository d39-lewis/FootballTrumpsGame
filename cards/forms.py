from django import forms

from .models import Card


class CardForm(forms.ModelForm):
    class Meta:
        model  = Card
        fields = [
            'player_name', 'rarity', 'image_url',
            'finishing', 'defending', 'sprinting',
            'strength', 'tech', 'leadership',
        ]
        widgets = {
            'player_name': forms.TextInput(attrs={'placeholder': 'e.g. Erling Haaland'}),
            'image_url':   forms.URLInput(attrs={'placeholder': 'https://…'}),
        }
        help_texts = {
            'image_url': 'Paste the URL of the AI-generated card image.',
        }
