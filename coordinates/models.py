from django.db import models
from django.utils import timezone
from .managers import CoordinatesManager


class Coordinates(models.Model):
    address = models.CharField(
        'адрес',
        max_length=200,
        unique=True,
    )
    lat = models.FloatField('широта', null=True, blank=True)
    lon = models.FloatField('долгота', null=True, blank=True)
    created_at = models.DateTimeField('дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    last_checked = models.DateTimeField('дата последней проверки', default=timezone.now)

    objects = CoordinatesManager()

    class Meta:
        verbose_name = 'координаты'
        verbose_name_plural = 'координаты'
        indexes = [
            models.Index(fields=['address']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.address} ({self.lat}, {self.lon})"

    def needs_refresh(self):
        return (timezone.now() - self.last_checked).days > 30
