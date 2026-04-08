"""
Management command: seed_cards
Creates 100 cards across 5 rarity tiers.
  Common: 50  |  Rare: 20  |  Ultra Rare: 15  |  Legendary: 10  |  Epic: 5
Safe to run multiple times — uses get_or_create on player_name + rarity.
"""

from django.core.management.base import BaseCommand

from cards.models import Card, Rarity

SEED_DATA = {
    # ── COMMON (50) ───────────────────────────────────────────────────────────
    Rarity.COMMON: [
        dict(player_name='Marcus Radford',       finishing=72, defending=40, sprinting=85, strength=72, tech=72, leadership=65),
        dict(player_name='Jake Grellish',         finishing=65, defending=42, sprinting=72, strength=68, tech=74, leadership=58),
        dict(player_name='Jaydon Sancher',        finishing=72, defending=38, sprinting=80, strength=58, tech=78, leadership=55),
        dict(player_name='Rahim Sterlingo',       finishing=74, defending=45, sprinting=88, strength=62, tech=76, leadership=60),
        dict(player_name='Rent Alex-Aron',        finishing=62, defending=76, sprinting=74, strength=65, tech=82, leadership=70),
        dict(player_name='Subject 49',            finishing=60, defending=40, sprinting=82, strength=68, tech=49, leadership=75),
        dict(player_name='Marquini',              finishing=32, defending=93, sprinting=77, strength=84, tech=50, leadership=84),
        dict(player_name='Jordan Pickforde',      finishing=20, defending=88, sprinting=52, strength=72, tech=60, leadership=75),
        dict(player_name='Kieran Tripper',        finishing=55, defending=78, sprinting=72, strength=62, tech=70, leadership=72),
        dict(player_name='Kalvin Phillipps',      finishing=52, defending=72, sprinting=68, strength=74, tech=65, leadership=68),
        dict(player_name='Ben Whyte',             finishing=45, defending=80, sprinting=65, strength=76, tech=62, leadership=70),
        dict(player_name='Conor Galloway',        finishing=62, defending=65, sprinting=72, strength=70, tech=68, leadership=66),
        dict(player_name='Ollie Watkynns',        finishing=76, defending=38, sprinting=74, strength=78, tech=68, leadership=62),
        dict(player_name='Eberechi Ezzy',         finishing=74, defending=42, sprinting=82, strength=62, tech=78, leadership=58),
        dict(player_name='Jarod Bowman',          finishing=72, defending=52, sprinting=80, strength=68, tech=72, leadership=62),
        dict(player_name='Matheus Kuna',          finishing=75, defending=40, sprinting=78, strength=72, tech=74, leadership=58),
        dict(player_name='Tino Livramenti',       finishing=58, defending=72, sprinting=84, strength=62, tech=68, leadership=60),
        dict(player_name='Antoni Gordan',         finishing=70, defending=45, sprinting=82, strength=65, tech=72, leadership=58),
        dict(player_name='Harvey Elliot',         finishing=68, defending=50, sprinting=72, strength=58, tech=75, leadership=62),
        dict(player_name='Levi Colwyll',          finishing=42, defending=78, sprinting=65, strength=72, tech=62, leadership=68),
        dict(player_name='Morgan Gibbs-Wright',   finishing=72, defending=60, sprinting=76, strength=68, tech=74, leadership=68),
        dict(player_name='Lewis Dunke',           finishing=40, defending=80, sprinting=60, strength=80, tech=58, leadership=72),
        dict(player_name='Marco Guey',            finishing=45, defending=78, sprinting=62, strength=76, tech=64, leadership=70),
        dict(player_name='Ivan Tonee',            finishing=78, defending=35, sprinting=72, strength=80, tech=65, leadership=60),
        dict(player_name='Dominic Calvert-Lewis', finishing=74, defending=32, sprinting=68, strength=82, tech=62, leadership=58),
        dict(player_name='Emil Smith-Rowey',      finishing=70, defending=45, sprinting=74, strength=60, tech=76, leadership=60),
        dict(player_name='Curtis Jonez',          finishing=65, defending=58, sprinting=72, strength=68, tech=70, leadership=65),
        dict(player_name='Noni Maduekke',         finishing=70, defending=42, sprinting=84, strength=60, tech=74, leadership=56),
        dict(player_name='Ezri Konza',            finishing=38, defending=78, sprinting=62, strength=76, tech=60, leadership=68),
        dict(player_name='Cody Gakpoe',           finishing=72, defending=48, sprinting=80, strength=68, tech=72, leadership=62),
        dict(player_name='Xavi Simonz',           finishing=72, defending=55, sprinting=76, strength=60, tech=80, leadership=65),
        dict(player_name='Dusan Vlahovitch',      finishing=78, defending=30, sprinting=68, strength=82, tech=62, leadership=60),
        dict(player_name='Gabriel Martynelli',    finishing=72, defending=40, sprinting=84, strength=62, tech=72, leadership=58),
        dict(player_name='William Salibah',       finishing=42, defending=82, sprinting=68, strength=74, tech=65, leadership=72),
        dict(player_name='Alex Zinchenkoo',       finishing=55, defending=74, sprinting=76, strength=60, tech=78, leadership=65),
        dict(player_name='Sandro Tohnali',        finishing=65, defending=68, sprinting=70, strength=74, tech=72, leadership=70),
        dict(player_name='Nicolo Barello',        finishing=70, defending=65, sprinting=74, strength=72, tech=76, leadership=72),
        dict(player_name='Federico Dimarca',      finishing=60, defending=68, sprinting=78, strength=62, tech=74, leadership=65),
        dict(player_name='Gianluca Mancino',      finishing=42, defending=80, sprinting=65, strength=74, tech=62, leadership=70),
        dict(player_name='Alessandro Bastone',    finishing=40, defending=82, sprinting=64, strength=78, tech=64, leadership=72),
        dict(player_name='Weston McKenny',        finishing=62, defending=65, sprinting=72, strength=74, tech=68, leadership=68),
        dict(player_name='Stefan De Vryj',        finishing=38, defending=80, sprinting=60, strength=78, tech=60, leadership=70),
        dict(player_name='Matteo Darmiano',       finishing=55, defending=76, sprinting=72, strength=66, tech=68, leadership=64),
        dict(player_name='Davide Frattezi',       finishing=65, defending=62, sprinting=74, strength=68, tech=70, leadership=68),
        dict(player_name='Arkadiusz Millik',      finishing=76, defending=30, sprinting=65, strength=78, tech=65, leadership=58),
        dict(player_name='Memphis De Pay',        finishing=74, defending=38, sprinting=78, strength=65, tech=76, leadership=60),
        dict(player_name='Christian Pulissic',    finishing=72, defending=45, sprinting=80, strength=62, tech=76, leadership=62),
        dict(player_name='Emerson Royale',        finishing=52, defending=74, sprinting=76, strength=65, tech=65, leadership=62),
        dict(player_name='Juan Cuadrao',          finishing=68, defending=45, sprinting=80, strength=60, tech=74, leadership=58),
        dict(player_name='Giovani Di Lorenz',     finishing=55, defending=75, sprinting=70, strength=64, tech=68, leadership=68),
    ],

    # ── RARE (20) ─────────────────────────────────────────────────────────────
    Rarity.RARE: [
        # Existing 5
        dict(player_name='Bruno Fernandez',       finishing=83, defending=55, sprinting=72, strength=68, tech=85, leadership=80),
        dict(player_name='Kevin De Bruynne',      finishing=85, defending=60, sprinting=74, strength=70, tech=90, leadership=85),
        dict(player_name='Virgil Van Dijke',      finishing=55, defending=92, sprinting=72, strength=88, tech=72, leadership=85),
        dict(player_name='Lautaro Martinezz',     finishing=86, defending=42, sprinting=78, strength=80, tech=76, leadership=72),
        dict(player_name='Pedrinho',              finishing=78, defending=62, sprinting=74, strength=62, tech=88, leadership=76),
        # 15 new rares
        dict(player_name='Toni Krooss',           finishing=72, defending=72, sprinting=65, strength=65, tech=92, leadership=88),
        dict(player_name='Luka Modritch',         finishing=75, defending=68, sprinting=70, strength=62, tech=90, leadership=88),
        dict(player_name='N\'Golo Kanti',         finishing=55, defending=90, sprinting=82, strength=76, tech=78, leadership=80),
        dict(player_name='Marquinnhos',           finishing=48, defending=90, sprinting=72, strength=80, tech=72, leadership=82),
        dict(player_name='Raphael Varani',        finishing=52, defending=88, sprinting=70, strength=84, tech=68, leadership=80),
        dict(player_name='Leroy Sanii',           finishing=80, defending=48, sprinting=92, strength=70, tech=82, leadership=68),
        dict(player_name='Thomas Mullar',         finishing=76, defending=52, sprinting=68, strength=65, tech=84, leadership=82),
        dict(player_name='Ilkay Gundoghan',       finishing=78, defending=62, sprinting=68, strength=68, tech=86, leadership=80),
        dict(player_name='Leon Goretska',         finishing=70, defending=72, sprinting=74, strength=80, tech=78, leadership=78),
        dict(player_name='Serge Gnabri',          finishing=82, defending=45, sprinting=88, strength=68, tech=80, leadership=68),
        dict(player_name='Roberto Firminoo',      finishing=84, defending=48, sprinting=80, strength=72, tech=82, leadership=74),
        dict(player_name='Sadio Manii',           finishing=82, defending=50, sprinting=88, strength=72, tech=80, leadership=76),
        dict(player_name='Kazimiro',              finishing=65, defending=88, sprinting=68, strength=82, tech=78, leadership=85),
        dict(player_name='Jonas Hofmanno',        finishing=75, defending=55, sprinting=78, strength=65, tech=78, leadership=70),
        dict(player_name='Giovanni Rezna',        finishing=72, defending=58, sprinting=76, strength=62, tech=80, leadership=68),
    ],

    # ── ULTRA RARE (15) ───────────────────────────────────────────────────────
    Rarity.ULTRA_RARE: [
        dict(player_name='Mo Salah',              finishing=90, defending=45, sprinting=92, strength=72, tech=85, leadership=78),
        dict(player_name='Harry Kayne',           finishing=92, defending=50, sprinting=78, strength=85, tech=82, leadership=88),
        dict(player_name='Vinicius Juniorr',      finishing=88, defending=42, sprinting=95, strength=68, tech=88, leadership=72),
        dict(player_name='Bukayo Sakka',          finishing=85, defending=65, sprinting=86, strength=70, tech=86, leadership=78),
        dict(player_name='Rodrigo Cascante',      finishing=68, defending=85, sprinting=72, strength=82, tech=88, leadership=90),
        dict(player_name='Heung-Min Sonn',        finishing=88, defending=55, sprinting=90, strength=68, tech=85, leadership=78),
        dict(player_name='Antoine Griezman',      finishing=88, defending=60, sprinting=82, strength=72, tech=86, leadership=82),
        dict(player_name='Karim Benzima',         finishing=90, defending=45, sprinting=80, strength=80, tech=88, leadership=84),
        dict(player_name='Federico Valverdee',    finishing=78, defending=72, sprinting=82, strength=78, tech=84, leadership=82),
        dict(player_name='Thibaut Courtoiz',      finishing=22, defending=92, sprinting=56, strength=78, tech=85, leadership=88),
        dict(player_name='Alisson Bekker',        finishing=20, defending=92, sprinting=55, strength=75, tech=82, leadership=85),
        dict(player_name='Achraf Hakkimi',        finishing=65, defending=82, sprinting=94, strength=70, tech=78, leadership=72),
        dict(player_name='Kvara Tskheliashvili',  finishing=86, defending=50, sprinting=88, strength=65, tech=90, leadership=74),
        dict(player_name='Raphinha Belloli',      finishing=84, defending=55, sprinting=88, strength=65, tech=84, leadership=72),
        dict(player_name='Ousmane Dembeli',       finishing=84, defending=42, sprinting=94, strength=62, tech=86, leadership=65),
    ],

    # ── LEGENDARY (10) ────────────────────────────────────────────────────────
    Rarity.LEGENDARY: [
        dict(player_name='Lionel Messii',         finishing=99, defending=75, sprinting=94, strength=80, tech=99, leadership=96),
        dict(player_name='Cristiano Ronaldoo',    finishing=98, defending=68, sprinting=97, strength=93, tech=93, leadership=96),
        dict(player_name='Neymar Juniorr',        finishing=98, defending=75, sprinting=96, strength=82, tech=98, leadership=92),
        dict(player_name='Zinedine Zidann',       finishing=93, defending=85, sprinting=88, strength=86, tech=98, leadership=96),
        dict(player_name='Ronaldinhoo',           finishing=98, defending=75, sprinting=94, strength=82, tech=99, leadership=94),
        dict(player_name='Erling Haalanddd',      finishing=99, defending=68, sprinting=98, strength=99, tech=86, leadership=92),
        dict(player_name='Kylian Mbappi',         finishing=98, defending=72, sprinting=99, strength=88, tech=95, leadership=92),
        dict(player_name='Thierry Henri',         finishing=98, defending=72, sprinting=98, strength=88, tech=94, leadership=93),
        dict(player_name='Ronahldoo',             finishing=99, defending=72, sprinting=97, strength=86, tech=98, leadership=92),
        dict(player_name='Diego Maradonna',       finishing=98, defending=75, sprinting=91, strength=84, tech=99, leadership=96),
    ],

    # ── EPIC (5) ──────────────────────────────────────────────────
    Rarity.EPIC: [
        dict(player_name='Lamine Yamall',         finishing=88, defending=55, sprinting=90, strength=65, tech=92, leadership=78),
        dict(player_name='Jude Bellinghem',       finishing=88, defending=75, sprinting=85, strength=82, tech=88, leadership=90),
        dict(player_name='Florian Wirtzz',        finishing=86, defending=58, sprinting=82, strength=68, tech=90, leadership=80),
        dict(player_name='Phil Fodenn',           finishing=88, defending=58, sprinting=82, strength=70, tech=90, leadership=78),
        dict(player_name='Declan Ricce',          finishing=72, defending=88, sprinting=78, strength=85, tech=82, leadership=88),
    ],
}


class Command(BaseCommand):
    help = 'Seed the database with 100 cards (Common 50, Rare 20, Ultra Rare 15, Epic 5, Legendary 10).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing cards before seeding.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            deleted, _ = Card.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing card(s).'))

        created_count = 0
        skipped_count = 0

        for rarity, players in SEED_DATA.items():
            for player in players:
                _, created = Card.objects.get_or_create(
                    player_name=player['player_name'],
                    rarity=rarity,
                    defaults={k: v for k, v in player.items() if k != 'player_name'},
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  Created: {player["player_name"]} ({rarity})')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(f'  Skipped (exists): {player["player_name"]} ({rarity})')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Created {created_count} cards, skipped {skipped_count} existing.'
            )
        )
