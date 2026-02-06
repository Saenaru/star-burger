from django.contrib import admin
from .models import Coordinates


@admin.register(Coordinates)
class CoordinatesAdmin(admin.ModelAdmin):
    list_display = ['address', 'lat', 'lon', 'created_at', 'last_checked']
    list_filter = ['created_at', 'last_checked']
    search_fields = ['address']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основное', {
            'fields': ('address', 'lat', 'lon')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'last_checked'),
            'classes': ('collapse',)
        }),
    )
