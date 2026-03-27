from django.contrib import admin
from django.utils.html import format_html

from .models import Card, CollectionItem, Rarity


RARITY_COLOURS = {
    Rarity.COMMON: '#9e9e9e',
    Rarity.RARE: '#2196f3',
    Rarity.ULTRA_RARE: '#9c27b0',
    Rarity.EPIC: '#ff5722',
    Rarity.LEGENDARY: '#ffc107',
}


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = [
        'player_name',
        'rarity_badge',
        'finishing',
        'defending',
        'sprinting',
        'strength',
        'tech',
        'leadership',
        'overall_rating',
        'has_image',
    ]
    list_filter = ['rarity']
    search_fields = ['player_name']
    readonly_fields = ['card_id', 'overall_rating']

    fieldsets = (
        (None, {
            'fields': ('card_id', 'player_name', 'rarity', 'image_url'),
        }),
        ('Gameplay Attributes', {
            'fields': ('finishing', 'defending', 'sprinting', 'strength', 'tech', 'leadership'),
        }),
    )

    @admin.display(description='Rarity')
    def rarity_badge(self, obj):
        colour = RARITY_COLOURS.get(obj.rarity, '#9e9e9e')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-weight:600;font-size:0.8rem;">{}</span>',
            colour,
            obj.get_rarity_display(),
        )

    @admin.display(description='Overall')
    def overall_rating(self, obj):
        return obj.overall

    @admin.display(description='Image', boolean=True)
    def has_image(self, obj):
        return bool(obj.image_url)


@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'card', 'quantity', 'date_obtained']
    list_filter = ['card__rarity']
    search_fields = ['user__email', 'card__player_name']
    readonly_fields = ['date_obtained']
