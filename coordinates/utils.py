import logging
from math import radians, sin, cos, sqrt, atan2
from .models import Coordinates

logger = logging.getLogger(__name__)


def get_coordinates(address):
    return Coordinates.objects.get_or_fetch_coordinates(address)


def calculate_distance(coords1, coords2):
    if not coords1 or not coords2:
        return None
    
    try:
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


def batch_get_coordinates(addresses):
    return Coordinates.objects.batch_get_coordinates(addresses)


def get_distance_between_addresses(address1, address2):
    coords1 = get_coordinates(address1)
    coords2 = get_coordinates(address2)
    
    if not coords1 or not coords2:
        return None
    
    return calculate_distance(coords1, coords2)