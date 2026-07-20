"""
Simple, deterministic rule-based outfit recommendation logic.

No machine learning or computer vision is used. Recommendations are generated
by filtering the user's wardrobe on category/season/occasion and pairing
compatible pieces together using straightforward matching rules.
"""
import random
from wardrobe.models import WardrobeItem

# Categories that make up a "complete" outfit, in priority order.
CORE_SLOTS = ["top", "bottom", "footwear"]
OPTIONAL_SLOTS = ["outerwear", "accessory", "headwear", "bag"]

# Neutral colors pair well with virtually anything -- used for simple color compatibility.
NEUTRAL_COLORS = {"black", "white", "grey", "gray", "navy", "beige", "brown", "cream", "khaki"}


def colors_compatible(color_a: str, color_b: str) -> bool:
    a, b = color_a.lower().strip(), color_b.lower().strip()
    if a == b:
        return True
    if a in NEUTRAL_COLORS or b in NEUTRAL_COLORS:
        return True
    return False


def build_outfit(user, season=None, occasion=None, exclude_ids=None):
    """
    Selects one item per core slot (top/bottom/footwear) that share the
    requested season & occasion and have broadly compatible colors, plus
    optional accent pieces. Returns (items_list, explanation_text) or (None, reason).
    """
    exclude_ids = exclude_ids or []
    base_qs = WardrobeItem.objects.filter(user=user).exclude(id__in=exclude_ids)

    if not base_qs.exists():
        return None, "No wardrobe items found. Try adding a few pieces to your wardrobe first."

    chosen = []
    anchor_color = None

    # Handle "dress" as an alternative to top+bottom.
    dresses = list(slot_candidates(base_qs, "dress", season, occasion))
    use_dress = bool(dresses) and random.random() < 0.35

    if use_dress:
        dress = random.choice(dresses)
        chosen.append(dress)
        anchor_color = dress.color
    else:
        for slot in ["top", "bottom"]:
            candidates = list(slot_candidates(base_qs, slot, season, occasion))
            if anchor_color:
                compatible = [c for c in candidates if colors_compatible(c.color, anchor_color)]
                candidates = compatible or candidates
            if not candidates:
                return None, f"Your wardrobe is missing a '{slot}' item for this season/occasion."
            pick = random.choice(candidates)
            chosen.append(pick)
            if not anchor_color:
                anchor_color = pick.color

    # Footwear
    footwear_candidates = list(slot_candidates(base_qs, "footwear", season, occasion))
    if footwear_candidates:
        compatible = [c for c in footwear_candidates if colors_compatible(c.color, anchor_color)]
        chosen.append(random.choice(compatible or footwear_candidates))

    # Optional accents (outerwear based on cold season, plus one accessory)
    if season in ("winter", "autumn", "rainy"):
        outerwear = list(slot_candidates(base_qs, "outerwear", season, occasion))
        if outerwear:
            compatible = [c for c in outerwear if colors_compatible(c.color, anchor_color)]
            chosen.append(random.choice(compatible or outerwear))

    for slot in ["accessory", "bag", "headwear"]:
        candidates = list(slot_candidates(base_qs, slot, season, occasion))
        if candidates and random.random() < 0.5:
            chosen.append(random.choice(candidates))

    explanation = _build_explanation(chosen, season, occasion)
    return chosen, explanation


def slot_candidates(base_qs, category, season=None, occasion=None):
    """Prefer requested season/occasion, then fall back to usable owned items in the slot."""
    candidates = base_qs.filter(category=category)

    if season and season != "all_season":
        season_matches = candidates.filter(models_season_filter(season))
        if season_matches.exists():
            candidates = season_matches

    if occasion:
        occasion_matches = candidates.filter(occasion=occasion)
        if occasion_matches.exists():
            return occasion_matches

    return candidates


def models_season_filter(season):
    """Match items tagged for the requested season OR flagged as all-season."""
    from django.db.models import Q
    return Q(season=season) | Q(season="all_season")


def _build_explanation(items, season, occasion):
    parts = []
    categories = ", ".join(sorted({i.get_category_display() for i in items}))
    parts.append(f"Paired {len(items)} pieces ({categories}) using matching neutral/complementary colors.")
    if season:
        parts.append(f"Filtered for {season.replace('_', ' ')} weather.")
    if occasion:
        parts.append(f"Suited for a {occasion} occasion.")
    return " ".join(parts)
