from django import template
from django.utils.safestring import mark_safe

from cards.svg import generate_card_svg

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def card_svg(card):
    """Render a full inline SVG trading card for the given Card instance."""
    return mark_safe(generate_card_svg(card))
