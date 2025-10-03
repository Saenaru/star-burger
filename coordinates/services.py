import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class YandexGeocoderService:
    @staticmethod
    def geocode_address(address):
        if not settings.YANDEX_GEOCODER_API_KEY:
            logger.warning("Yandex Geocoder API key not set")
            return None
        if not address or not address.strip():
            return None
        try:
            base_url = "https://geocode-maps.yandex.ru/1.x"
            params = {
                'geocode': address.strip(),
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
            return (lat, lon)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during geocoding for address '{address}': {e}")
            return None
        except Exception as e:
            logger.error(f"Geocoding error for address '{address}': {e}")
            return None