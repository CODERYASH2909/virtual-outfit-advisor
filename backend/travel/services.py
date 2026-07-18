"""
Weather API integration and simple rule-based packing/outfit suggestion logic.

Only the OpenWeatherMap Weather API is used for external data. All packing
and outfit suggestions are generated with plain conditional rules -- no ML,
no computer vision, no other third-party services.
"""
import requests
from django.conf import settings


class WeatherAPIError(Exception):
    pass


def fetch_weather_forecast(city: str = "", country: str = "", lat: float = None, lon: float = None):
    """
    Calls OpenWeatherMap's 5-day/3-hour forecast endpoint and returns a
    simplified summary: avg/min/max temperature (Celsius) and a dominant
    weather condition label.
    """
    if not settings.WEATHER_API_KEY:
        raise WeatherAPIError("Weather API key is not configured on the server.")

    url = f"{settings.WEATHER_API_BASE_URL}/forecast"
    if lat is not None and lon is not None:
        params = {"lat": lat, "lon": lon, "appid": settings.WEATHER_API_KEY, "units": "metric"}
    else:
        query = f"{city},{country}" if country else city
        params = {"q": query, "appid": settings.WEATHER_API_KEY, "units": "metric"}

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.RequestException as exc:
        raise WeatherAPIError(f"Could not reach weather service: {exc}")

    if response.status_code != 200:
        try:
            error_data = response.json()
            error_msg = error_data.get("message", response.text)
        except Exception:
            error_msg = response.text
        location_str = f"coords ({lat}, {lon})" if (lat is not None and lon is not None) else f"'{city}'"
        raise WeatherAPIError(f"Weather service returned an error for {location_str}: {error_msg}")

    data = response.json()
    entries = data.get("list", [])
    if not entries:
        raise WeatherAPIError("No forecast data available for this location.")

    temps = [e["main"]["temp"] for e in entries]
    conditions = [e["weather"][0]["main"] for e in entries if e.get("weather")]
    dominant_condition = max(set(conditions), key=conditions.count) if conditions else "Clear"

    resolved_city = data.get("city", {}).get("name", city)
    resolved_country = data.get("city", {}).get("country", country)

    return {
        "city": resolved_city,
        "country": resolved_country,
        "avg_temperature_c": round(sum(temps) / len(temps), 1),
        "min_temperature_c": round(min(temps), 1),
        "max_temperature_c": round(max(temps), 1),
        "weather_condition": dominant_condition,
        "weather_summary": (
            f"Expect {dominant_condition.lower()} conditions with temperatures "
            f"ranging from {round(min(temps), 1)}°C to {round(max(temps), 1)}°C."
        ),
    }


def infer_season_from_temp(avg_temp: float) -> str:
    if avg_temp is None:
        return "all_season"
    if avg_temp >= 25:
        return "summer"
    if avg_temp >= 15:
        return "spring"
    if avg_temp >= 5:
        return "autumn"
    return "winter"


# Base packing checklist items, expanded conditionally below.
BASE_PACKING_LIST = [
    "Underwear (1 per day)", "Socks (1 per day)", "Sleepwear",
    "Toiletries kit", "Phone charger", "Travel documents / ID",
]

CONDITION_PACKING_RULES = {
    "Rain": ["Waterproof jacket", "Compact umbrella", "Water-resistant shoes"],
    "Snow": ["Insulated winter coat", "Thermal base layers", "Waterproof boots", "Gloves", "Beanie"],
    "Clear": ["Sunglasses", "Sunscreen", "Hat/cap"],
    "Clouds": ["Light layering jacket"],
    "Thunderstorm": ["Waterproof jacket", "Umbrella", "Power bank (for storm outages)"],
    "Drizzle": ["Light raincoat", "Umbrella"],
    "Mist": ["Light jacket"],
    "Haze": ["Light scarf/mask for sensitive travelers"],
}

TEMP_PACKING_RULES = [
    (30, ["Light breathable t-shirts", "Shorts", "Sandals", "Sun hat"]),
    (20, ["T-shirts", "Light trousers/jeans", "Light sneakers"]),
    (10, ["Sweaters", "Long-sleeve shirts", "Medium jacket", "Jeans"]),
    (0, ["Heavy coat", "Thermal wear", "Warm scarf", "Gloves", "Insulated boots"]),
]

PURPOSE_PACKING_RULES = {
    "business": ["Formal blazer", "Dress shirts", "Formal shoes", "Laptop & charger"],
    "beach": ["Swimsuit", "Beach towel", "Flip-flops", "After-sun lotion"],
    "winter_sports": ["Thermal ski layers", "Waterproof gloves", "Snow goggles"],
    "adventure": ["Hiking boots", "Quick-dry clothing", "Backpack"],
}


def build_packing_list(avg_temp, weather_condition, trip_purpose, duration_days):
    packing = list(BASE_PACKING_LIST)

    for threshold, items in TEMP_PACKING_RULES:
        if avg_temp is not None and avg_temp >= threshold:
            packing.extend(items)
            break
    else:
        packing.extend(TEMP_PACKING_RULES[-1][1])

    packing.extend(CONDITION_PACKING_RULES.get(weather_condition, []))
    packing.extend(PURPOSE_PACKING_RULES.get(trip_purpose, []))

    if duration_days and duration_days > 5:
        packing.append("Laundry bag (longer trip)")

    # Deduplicate while preserving order.
    seen = set()
    unique_packing = []
    for item in packing:
        if item not in seen:
            unique_packing.append(item)
            seen.add(item)
    return unique_packing


def build_outfit_suggestions_from_wardrobe(user, season, occasion="travel"):
    """Reuses the same rule-based outfit builder from the recommendations app."""
    from recommendations.services import build_outfit
    items, explanation = build_outfit(user, season=season, occasion=occasion)
    if items is None:
        # Fall back to casual if no travel-tagged items exist.
        items, explanation = build_outfit(user, season=season, occasion="casual")
    if items is None:
        return []
    return [{"id": i.id, "name": i.name, "category": i.category, "image": i.image.url if i.image else None} for i in items]
