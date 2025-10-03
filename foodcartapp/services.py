from coordinates.utils import get_distance_between_addresses
from coordinates.models import Coordinates


def get_order_coordinates(order):
    return Coordinates.objects.get_or_fetch_coordinates(order.address)


def get_restaurant_coordinates(restaurant):
    return Coordinates.objects.get_or_fetch_coordinates(restaurant.address)


def calculate_order_restaurant_distance(order, restaurant):
    order_coords = get_order_coordinates(order)
    restaurant_coords = get_restaurant_coordinates(restaurant)
    if not order_coords or not restaurant_coords:
        return None
    return get_distance_between_addresses(order.address, restaurant.address)
