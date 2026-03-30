from django.contrib import admin
from django.utils.html import format_html

from .models import Card, CollectionItem, Rarity

RARITY_COLOURS = {
    Rarity.COMMON:    '#9e9e9e',
    Rarity.RARE:      '#2196f3',
    Rarity.ULTRA_RARE:'#9c27b0',
    Rarity.EPIC:      '#7c3aed',
    Rarity.LEGENDARY: '#ffc107',
}


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display  = ['player_name', 'rarity_badge', 'finishing', 'defending',
                     'sprinting', 'strength', 'tech', 'leadership',
                     'overall_rating', 'image_preview_thumb']
    list_filter   = ['rarity']
    search_fields = ['player_name']
    readonly_fields = ['card_id', 'overall_rating', 'image_preview']

    fieldsets = (
        (None, {
            'fields': ('card_id', 'player_name', 'rarity'),
        }),
        ('Card Image', {
            'fields': ('image_url', 'image_preview'),
            'description': 'Paste the AI-generated image URL below. '
                           'The preview will update after saving.',
        }),
        ('Gameplay Attributes (0 – 99)', {
            'fields': (
                ('finishing', 'defending'),
                ('sprinting', 'strength'),
                ('tech',      'leadership'),
            ),
        }),
    )

    # ── Custom columns ────────────────────────────────────────────────────────

    @admin.display(description='Rarity')
    def rarity_badge(self, obj):
        colour = RARITY_COLOURS.get(obj.rarity, '#9e9e9e')
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;'
            'border-radius:4px;font-weight:700;font-size:0.78rem;">{}</span>',
            colour,
            '#111' if obj.rarity == Rarity.LEGENDARY else '#fff',
            obj.get_rarity_display(),
        )

    @admin.display(description='OVR')
    def overall_rating(self, obj):
        return obj.overall

    @admin.display(description='Image')
    def image_preview_thumb(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px;">', obj.image_url
            )
        return '—'

    @admin.display(description='Image preview')
    def image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-height:220px;max-width:180px;'
                'border-radius:8px;margin-top:6px;border:1px solid #ddd;">',
                obj.image_url,
            )
        return 'No image URL set yet.'


@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display  = ['user', 'card', 'quantity', 'date_obtained']
    list_filter   = ['card__rarity']
    search_fields = ['user__email', 'card__player_name']
    readonly_fields = ['date_obtained']
