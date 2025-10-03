import logging
from geopy.distance import distance
from .models import Coordinates

logger = logging.getLogger(__name__)


def calculate_distance(coords1, coords2):
    if not coords1 or not coords2:
        return None
    try:
        dist = distance(coords1, coords2).km
        return round(dist, 2)
    except Exception as e:
        logger.error(f"Distance calculation error: {e}")
        return None


def get_distance_between_addresses(address1, address2):
    coords1 = Coordinates.objects.get_or_fetch_coordinates(address1)
    coords2 = Coordinates.objects.get_or_fetch_coordinates(address2)
    if not coords1 or not coords2:
        return None
    return calculate_distance(coords1, coords2)