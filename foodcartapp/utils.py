import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def get_coordinates(address):
    if not address or not address.strip():
        return None
    cache_key = f"coordinates_{address.strip()}"
    cached_coords = cache.get(cache_key)
    if cached_coords:
        return cached_coords
    if not settings.YANDEX_GEOCODER_API_KEY:
        logger.warning("Yandex Geocoder API key not set")
        return None
    try:
        base_url = "https://geocode-maps.yandex.ru/1.x"
        params = {
            'geocode': address,
            'apikey': settings.YANDEX_GEOCODER_API_KEY,
            'format': 'json',
            'results': 1
        }
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        features = data['response']['GeoObjectCollection']['featureMember']
        if not features:
            logger.warning(f"No coordinates found for address: {address}")
            return None
        pos = features[0]['GeoObject']['Point']['pos']
        lon, lat = map(float, pos.split())
        coords = (lat, lon)
        cache.set(cache_key, coords, 60*60*24)
        return coords
    except Exception as e:
        logger.error(f"Geocoding error for address '{address}': {e}")
        return None


def calculate_distance(coords1, coords2):
    if not coords1 or not coords2:
        return None
    try:
        from math import radians, sin, cos, sqrt, atan2
        lat1, lon1 = radians(coords1[0]), radians(coords1[1])
        lat2, lon2 = radians(coords2[0]), radians(coords2[1])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        R = 6371
        distance_km = R * c
        return round(distance_km, 2)
    except Exception as e:
        logger.error(f"Distance calculation error: {e}")
        return None
