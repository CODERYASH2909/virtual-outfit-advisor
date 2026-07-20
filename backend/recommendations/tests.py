from django.contrib.auth import get_user_model
from django.test import TestCase

from wardrobe.models import WardrobeItem
from .services import build_outfit


class BuildOutfitTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def add_item(self, name, category, color="black", season="all_season", occasion="casual"):
        return WardrobeItem.objects.create(
            user=self.user,
            name=name,
            category=category,
            color=color,
            season=season,
            occasion=occasion,
        )

    def test_falls_back_to_owned_slot_item_when_requested_occasion_is_missing(self):
        top = self.add_item("White T-Shirt", "top", color="white", occasion="casual")
        bottom = self.add_item("Black Trousers", "bottom", color="black", occasion="formal")
        footwear = self.add_item("Black Shoes", "footwear", color="black", occasion="formal")

        items, explanation = build_outfit(self.user, season="all_season", occasion="formal")

        self.assertIsNotNone(items, explanation)
        self.assertIn(top, items)
        self.assertIn(bottom, items)
        self.assertIn(footwear, items)

    def test_prefers_requested_occasion_when_available_for_slot(self):
        casual_top = self.add_item("Casual T-Shirt", "top", color="white", occasion="casual")
        formal_top = self.add_item("Formal Shirt", "top", color="white", occasion="formal")
        self.add_item("Black Trousers", "bottom", color="black", occasion="formal")
        self.add_item("Black Shoes", "footwear", color="black", occasion="formal")

        items, explanation = build_outfit(self.user, season="all_season", occasion="formal")

        self.assertIsNotNone(items, explanation)
        self.assertIn(formal_top, items)
        self.assertNotIn(casual_top, items)

    def test_falls_back_to_owned_slot_item_when_requested_season_is_missing(self):
        top = self.add_item("Summer T-Shirt", "top", color="white", season="summer")
        bottom = self.add_item("Jeans", "bottom", color="black", season="all_season")
        footwear = self.add_item("Sneakers", "footwear", color="black", season="all_season")

        items, explanation = build_outfit(self.user, season="rainy", occasion="casual")

        self.assertIsNotNone(items, explanation)
        self.assertIn(top, items)
        self.assertIn(bottom, items)
        self.assertIn(footwear, items)
