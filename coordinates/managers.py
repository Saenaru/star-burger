from django.db import models
from django.utils import timezone
import logging
from .services import geocode_address

logger = logging.getLogger(__name__)


class CoordinatesManager(models.Manager):
    def get_or_fetch_coordinates(self, address):
        if not address or not address.strip():
            return None
        address = address.strip()
        try:
            coords_obj = self.get(address=address)
            return (coords_obj.lat, coords_obj.lon)
        except self.model.DoesNotExist:
            pass
        coordinates = geocode_address(address)
        if coordinates:
            self.create(
                address=address,
                lat=coordinates[0],
                lon=coordinates[1]
            )
            return coordinates
        return None

    def batch_get_coordinates(self, addresses):
        if not addresses:
            return {}
        clean_addresses = [addr.strip() for addr in addresses if addr and addr.strip()]
        if not clean_addresses:
            return {}
        coordinates = {}
        addresses_to_fetch = []
        existing_coords = self.filter(address__in=clean_addresses)
        coords_by_address = {obj.address: obj for obj in existing_coords}
        if existing_coords:
            now = timezone.now()
            self.filter(id__in=[obj.id for obj in existing_coords]).update(last_checked=now)
        for address in clean_addresses:
            if address in coords_by_address:
                coords_obj = coords_by_address[address]
                coordinates[address] = (coords_obj.lat, coords_obj.lon)
            else:
                addresses_to_fetch.append(address)
        if addresses_to_fetch:
            new_coords_objects = []
            for address in addresses_to_fetch:
                coords = geocode_address(address)
                if coords:
                    coordinates[address] = coords
                    new_coords_objects.append(self.model(
                        address=address,
                        lat=coords[0],
                        lon=coords[1]
                    ))
            if new_coords_objects:
                self.bulk_create(new_coords_objects)
        return coordinates
