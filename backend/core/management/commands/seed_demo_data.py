"""
Management command to seed a demo user with sample wardrobe items so the
app can be explored immediately after setup.

Usage: python manage.py seed_demo_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wardrobe.models import WardrobeItem

User = get_user_model()

SAMPLE_ITEMS = [
    ("White Cotton T-Shirt", "top", "white", "all_season", "casual"),
    ("Blue Denim Jeans", "bottom", "blue", "all_season", "casual"),
    ("Black Leather Jacket", "outerwear", "black", "autumn", "casual"),
    ("Grey Wool Sweater", "top", "grey", "winter", "casual"),
    ("White Sneakers", "footwear", "white", "all_season", "casual"),
    ("Black Formal Blazer", "outerwear", "black", "all_season", "business"),
    ("Navy Dress Shirt", "top", "navy", "all_season", "business"),
    ("Black Formal Trousers", "bottom", "black", "all_season", "business"),
    ("Brown Leather Shoes", "footwear", "brown", "all_season", "business"),
    ("Floral Summer Dress", "dress", "multicolor", "summer", "casual"),
    ("Straw Sun Hat", "headwear", "beige", "summer", "beach"),
    ("Beach Sandals", "footwear", "tan", "summer", "beach"),
    ("Insulated Winter Coat", "outerwear", "black", "winter", "casual"),
    ("Wool Beanie", "headwear", "grey", "winter", "casual"),
    ("Running Shorts", "bottom", "black", "summer", "sports"),
    ("Sports Sneakers", "footwear", "black", "all_season", "sports"),
]


class Command(BaseCommand):
    help = "Seed a demo user with sample wardrobe items."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email="demo@voa.local",
            defaults={"username": "demo_user", "first_name": "Demo", "last_name": "User"},
        )
        if created:
            user.set_password("DemoPass123!")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created demo user: demo@voa.local / DemoPass123!"))
        else:
            self.stdout.write("Demo user already exists.")

        created_count = 0
        for name, category, color, season, occasion in SAMPLE_ITEMS:
            _, was_created = WardrobeItem.objects.get_or_create(
                user=user, name=name,
                defaults={"category": category, "color": color, "season": season, "occasion": occasion},
            )
            created_count += 1 if was_created else 0

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} new wardrobe items for demo user."))
