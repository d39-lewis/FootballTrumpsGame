"""
SVG card generator.
Returns a complete inline SVG string for a Card instance.
"""

from django.utils.html import escape

from .models import Rarity

# Colour scheme per rarity — matches the CSS card classes in rarity_detail.html
RARITY_STYLES = {
    Rarity.COMMON: {
        'grad_top':     '#5a2e0a',
        'grad_mid':     '#3b1c08',
        'grad_bot':     '#1a0a02',
        'border':       '#cd8c3c',
        'header_bg':    'rgba(0,0,0,0.45)',
        'img_bg_a':     'rgba(139,90,43,0.30)',
        'img_bg_b':     'rgba(60,30,5,0.55)',
        'name_bg':      'rgba(139,90,43,0.60)',
        'stats_bg':     'rgba(0,0,0,0.40)',
        'divider':      'rgba(205,140,60,0.35)',
        'ovr_col':      '#f5deb3',
        'label_col':    '#cd8c3c',
        'name_col':     '#fff8f0',
        'stat_lbl':     'rgba(232,196,154,0.70)',
        'stat_val':     '#e8c49a',
        'glow':         'rgba(139,90,43,0.0)',
        'label':        'COMMON',
        'shine_a':      'rgba(255,200,100,0.12)',
    },
    Rarity.RARE: {
        'grad_top':     '#3a3a3a',
        'grad_mid':     '#2a2a2a',
        'grad_bot':     '#111111',
        'border':       '#c8c8c8',
        'header_bg':    'rgba(0,0,0,0.50)',
        'img_bg_a':     'rgba(160,160,160,0.22)',
        'img_bg_b':     'rgba(60,60,60,0.50)',
        'name_bg':      'rgba(100,100,100,0.60)',
        'stats_bg':     'rgba(0,0,0,0.40)',
        'divider':      'rgba(200,200,200,0.30)',
        'ovr_col':      '#e8e8e8',
        'label_col':    '#c0c0c0',
        'name_col':     '#ffffff',
        'stat_lbl':     'rgba(212,212,212,0.65)',
        'stat_val':     '#d4d4d4',
        'glow':         'rgba(160,160,160,0.0)',
        'label':        'RARE',
        'shine_a':      'rgba(255,255,255,0.10)',
    },
    Rarity.ULTRA_RARE: {
        'grad_top':     '#3a2e00',
        'grad_mid':     '#2a1f00',
        'grad_bot':     '#0f0900',
        'border':       '#ffd700',
        'header_bg':    'rgba(0,0,0,0.50)',
        'img_bg_a':     'rgba(255,215,0,0.18)',
        'img_bg_b':     'rgba(120,80,0,0.50)',
        'name_bg':      'rgba(184,134,11,0.65)',
        'stats_bg':     'rgba(0,0,0,0.42)',
        'divider':      'rgba(255,215,0,0.28)',
        'ovr_col':      '#ffd700',
        'label_col':    '#ffd700',
        'name_col':     '#ffe680',
        'stat_lbl':     'rgba(255,230,128,0.65)',
        'stat_val':     '#ffe680',
        'glow':         'rgba(255,215,0,0.35)',
        'label':        'ULTRA RARE',
        'shine_a':      'rgba(255,215,0,0.15)',
    },
    Rarity.LEGENDARY: {
        'grad_top':     '#2a1a00',
        'grad_mid':     '#1a1000',
        'grad_bot':     '#050300',
        'border':       '#e8a800',
        'header_bg':    'rgba(0,0,0,0.40)',
        'img_bg_a':     'rgba(255,200,0,0.22)',
        'img_bg_b':     'rgba(80,50,0,0.55)',
        'name_bg':      'rgba(122,85,0,0.70)',
        'stats_bg':     'rgba(0,0,0,0.40)',
        'divider':      'rgba(232,168,0,0.30)',
        'ovr_col':      '#ffc200',
        'label_col':    '#ffc200',
        'name_col':     '#fff8e0',
        'stat_lbl':     'rgba(255,208,96,0.65)',
        'stat_val':     '#ffd060',
        'glow':         'rgba(255,180,0,0.50)',
        'label':        'LEGENDARY',
        'shine_a':      'rgba(255,200,0,0.20)',
    },
    Rarity.EPIC: {
        'grad_top':     '#1a0a2e',
        'grad_mid':     '#0d0d1a',
        'grad_bot':     '#050508',
        'border':       '#a78bfa',
        'header_bg':    'rgba(0,0,0,0.55)',
        'img_bg_a':     'rgba(167,139,250,0.18)',
        'img_bg_b':     'rgba(40,20,80,0.55)',
        'name_bg':      'rgba(76,29,149,0.65)',
        'stats_bg':     'rgba(0,0,0,0.45)',
        'divider':      'rgba(167,139,250,0.28)',
        'ovr_col':      '#c4b5fd',
        'label_col':    '#a78bfa',
        'name_col':     '#e9d5ff',
        'stat_lbl':     'rgba(196,181,253,0.65)',
        'stat_val':     '#c4b5fd',
        'glow':         'rgba(167,139,250,0.45)',
        'label':        'EPIC',
        'shine_a':      'rgba(167,139,250,0.18)',
    },
}


def _esc(text, max_len=20):
    text = text[:max_len] + ('…' if len(text) > max_len else '')
    return escape(text)


def generate_card_svg(card):
    """Return an inline SVG string for the given Card."""
    s = RARITY_STYLES.get(card.rarity, RARITY_STYLES[Rarity.COMMON])

    name    = _esc(card.player_name, 20)
    overall = card.overall
    has_img = bool(card.image_url)
    img_url = escape(card.image_url) if has_img else ''

    stats = [
        ('FIN', card.finishing),
        ('DEF', card.defending),
        ('SPR', card.sprinting),
        ('STR', card.strength),
        ('TEC', card.tech),
        ('LDR', card.leadership),
    ]

    # 3 columns, 2 rows
    col_cx = [34, 100, 166]
    row_label_y = [224, 260]
    row_val_y   = [240, 276]

    # Unique gradient IDs per card to avoid collisions when multiple SVGs are inline
    uid = str(card.card_id).replace('-', '')[:12]

    parts = [
        f'<svg viewBox="0 0 200 288" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink"'
        f' style="display:block;width:100%;height:auto;">',

        # ── Defs ──────────────────────────────────────────────────────────
        '<defs>',

        # Background gradient
        f'<linearGradient id="bg{uid}" x1="30%" y1="0%" x2="70%" y2="100%">',
        f'  <stop offset="0%"   stop-color="{s["grad_top"]}"/>',
        f'  <stop offset="50%"  stop-color="{s["grad_mid"]}"/>',
        f'  <stop offset="100%" stop-color="{s["grad_bot"]}"/>',
        '</linearGradient>',

        # Shine overlay
        f'<linearGradient id="sh{uid}" x1="0%" y1="0%" x2="30%" y2="100%">',
        f'  <stop offset="0%"  stop-color="{s["shine_a"]}"/>',
        f'  <stop offset="55%" stop-color="rgba(255,255,255,0)"/>',
        '</linearGradient>',

        # Image-area background gradient
        f'<linearGradient id="ib{uid}" x1="0%" y1="0%" x2="100%" y2="100%">',
        f'  <stop offset="0%"   stop-color="{s["img_bg_a"]}"/>',
        f'  <stop offset="100%" stop-color="{s["img_bg_b"]}"/>',
        '</linearGradient>',

        # Image fade at bottom (readability for name)
        f'<linearGradient id="if{uid}" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'  <stop offset="50%" stop-color="rgba(0,0,0,0)"/>',
        f'  <stop offset="100%" stop-color="rgba(0,0,0,0.65)"/>',
        '</linearGradient>',

        # Clip paths
        f'<clipPath id="cc{uid}"><rect width="200" height="288" rx="12"/></clipPath>',
        f'<clipPath id="ic{uid}"><rect x="0" y="50" width="200" height="128"/></clipPath>',

        '</defs>',

        # ── Card background ───────────────────────────────────────────────
        f'<rect width="200" height="288" rx="12" fill="url(#bg{uid})"/>',
        f'<rect width="200" height="288" rx="12" fill="url(#sh{uid})"/>',

        # Glow border effect (behind outer border)
        f'<rect x="0" y="0" width="200" height="288" rx="12" fill="none"'
        f' stroke="{s["glow"]}" stroke-width="8" opacity="0.6"/>',

        # Outer border
        f'<rect x="1.5" y="1.5" width="197" height="285" rx="11" fill="none"'
        f' stroke="{s["border"]}" stroke-width="2.5" opacity="0.90"/>',

        # Inner border (fine line)
        f'<rect x="5" y="5" width="190" height="278" rx="8" fill="none"'
        f' stroke="{s["border"]}" stroke-width="0.7" opacity="0.30"/>',

        # ── Header bar ────────────────────────────────────────────────────
        f'<rect x="0" y="0" width="200" height="52" rx="12" fill="{s["header_bg"]}"'
        f' clip-path="url(#cc{uid})"/>',
        f'<line x1="0" y1="52" x2="200" y2="52"'
        f' stroke="{s["border"]}" stroke-width="1" opacity="0.50"/>',

        # OVR number
        f'<text x="14" y="28" font-family="\'Segoe UI\',Arial,sans-serif"'
        f' font-size="24" font-weight="900" fill="{s["ovr_col"]}">{overall}</text>',
        f'<text x="14" y="42" font-family="\'Segoe UI\',Arial,sans-serif"'
        f' font-size="8" font-weight="700" letter-spacing="2"'
        f' fill="{s["ovr_col"]}" opacity="0.65">OVR</text>',

        # Rarity label
        f'<text x="188" y="30" font-family="\'Segoe UI\',Arial,sans-serif"'
        f' font-size="8" font-weight="900" letter-spacing="1.5"'
        f' fill="{s["label_col"]}" text-anchor="end">{s["label"]}</text>',
    ]

    # ── Image / silhouette area ───────────────────────────────────────────
    parts += [
        f'<rect x="0" y="50" width="200" height="128" fill="url(#ib{uid})"/>',
    ]

    if has_img:
        parts += [
            f'<image href="{img_url}" x="0" y="50" width="200" height="128"'
            f' clip-path="url(#ic{uid})" preserveAspectRatio="xMidYMid slice"/>',
            f'<rect x="0" y="50" width="200" height="128"'
            f' fill="url(#if{uid})" clip-path="url(#ic{uid})"/>',
        ]
    else:
        # Football player silhouette
        parts += [
            f'<g clip-path="url(#ic{uid})" opacity="0.32" fill="{s["border"]}">',
            # Head
            f'  <circle cx="100" cy="82" r="20"/>',
            # Body
            f'  <path d="M68,104 C68,104 72,142 100,144 C128,142 132,104 132,104 L127,102 C118,130 82,130 73,102 Z"/>',
            # Left arm
            f'  <line x1="74" y1="112" x2="54" y2="136" stroke="{s["border"]}" stroke-width="10" stroke-linecap="round"/>',
            # Right arm (raised for kick)
            f'  <line x1="126" y1="112" x2="148" y2="128" stroke="{s["border"]}" stroke-width="10" stroke-linecap="round"/>',
            # Left leg
            f'  <line x1="86" y1="140" x2="78" y2="172" stroke="{s["border"]}" stroke-width="11" stroke-linecap="round"/>',
            # Right leg (kicking)
            f'  <path d="M114,140 L132,162 L158,158" stroke="{s["border"]}" stroke-width="11"'
            f'   stroke-linecap="round" stroke-linejoin="round" fill="none"/>',
            # Ball
            f'  <circle cx="157" cy="157" r="13"/>',
            f'  <polygon points="157,146 164,152 162,162 152,162 149,152" fill="rgba(0,0,0,0.35)"/>',
            '</g>',
        ]

    # ── Name plate ────────────────────────────────────────────────────────
    parts += [
        f'<rect x="0" y="178" width="200" height="26" fill="{s["name_bg"]}"/>',
        f'<line x1="0" y1="178" x2="200" y2="178"'
        f' stroke="{s["border"]}" stroke-width="0.8" opacity="0.45"/>',
        f'<line x1="0" y1="204" x2="200" y2="204"'
        f' stroke="{s["border"]}" stroke-width="0.8" opacity="0.45"/>',
        f'<text x="100" y="195" font-family="\'Segoe UI\',Arial,sans-serif"'
        f' font-size="11.5" font-weight="800" fill="{s["name_col"]}" text-anchor="middle">{name}</text>',
    ]

    # ── Stats area ────────────────────────────────────────────────────────
    parts += [
        f'<rect x="0" y="204" width="200" height="84" fill="{s["stats_bg"]}" clip-path="url(#cc{uid})"/>',
        # Vertical dividers
        f'<line x1="67" y1="210" x2="67" y2="282" stroke="{s["divider"]}" stroke-width="0.8"/>',
        f'<line x1="133" y1="210" x2="133" y2="282" stroke="{s["divider"]}" stroke-width="0.8"/>',
        # Horizontal divider between stat rows
        f'<line x1="8" y1="248" x2="192" y2="248" stroke="{s["divider"]}" stroke-width="0.8"/>',
    ]

    for i, (lbl, val) in enumerate(stats):
        col = i % 3
        row = i // 3
        x  = col_cx[col]
        ly = row_label_y[row]
        vy = row_val_y[row]
        parts += [
            f'<text x="{x}" y="{ly}" font-family="\'Segoe UI\',Arial,sans-serif"'
            f' font-size="8.5" font-weight="700" letter-spacing="0.8"'
            f' fill="{s["stat_lbl"]}" text-anchor="middle">{lbl}</text>',
            f'<text x="{x}" y="{vy}" font-family="\'Segoe UI\',Arial,sans-serif"'
            f' font-size="15" font-weight="900"'
            f' fill="{s["stat_val"]}" text-anchor="middle">{val}</text>',
        ]

    parts.append('</svg>')
    return '\n'.join(parts)
