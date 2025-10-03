from django.contrib import admin
from django.shortcuts import reverse, redirect
from django.templatetags.static import static
from django.utils.html import format_html
from django.db.models import Sum, F, Count
from django.utils import timezone
from django.contrib import messages


from .models import Product, ProductCategory, Restaurant, RestaurantMenuItem, Order, OrderItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address', 'contact_phone']
    list_display = ['name', 'address', 'contact_phone']
    inlines = [RestaurantMenuItemInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['get_image_list_preview', 'name', 'category', 'price']
    list_display_links = ['name']
    list_filter = ['category']
    search_fields = ['name', 'category__name']
    inlines = [RestaurantMenuItemInline]
    fieldsets = (
        ('Общее', {'fields': ['name', 'category', 'image', 'get_image_preview', 'price']}),
        ('Подробно', {'fields': ['special_status', 'description'], 'classes': ['wide']}),
    )
    readonly_fields = ['get_image_preview']

    class Media:
        css = {"all": (static("admin/foodcartapp.css"))}

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    pass


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'firstname',
        'lastname',
        'phonenumber',
        'address',
        'status',
        'assigned_restaurant',
        'created_at',
        'called_at',
        'delivered_at',
        'get_items_count',
        'get_total_display'
    ]
    list_editable = ['status']
    list_filter = ['status', 'created_at', 'payment_method', 'called_at', 'delivered_at']
    search_fields = ['firstname', 'lastname', 'phonenumber', 'address']
    readonly_fields = ['created_at']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Клиент', {'fields': ('firstname', 'lastname', 'phonenumber', 'address')}),
        ('Заказ', {'fields': ('status', 'payment_method', 'comment', 'assigned_restaurant')}),
        ('Временные метки', {
            'fields': ('created_at', 'called_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            try:
                old_obj = Order.objects.get(pk=obj.pk)
                if (obj.status == 'processing' and 
                    old_obj.status != 'processing' and 
                    not obj.called_at):
                    obj.called_at = timezone.now()
                if (obj.status == 'completed' and 
                    old_obj.status != 'completed' and 
                    not obj.delivered_at):
                    obj.delivered_at = timezone.now()
                if (obj.status == 'cancelled' and 
                    old_obj.status != 'cancelled'):
                    obj.called_at = None
                    obj.delivered_at = None
            except Order.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'assigned_restaurant'
        ).prefetch_related(
            'items',
            'items__product'
        ).annotate(
            total_price=Sum(F('items__quantity') * F('items__price')),
            items_count=Count('items')
        )

    def get_items_count(self, obj):
        if hasattr(obj, 'items_count') and obj.items_count is not None:
            return obj.items_count
        return obj.items.count()
    get_items_count.short_description = 'кол-во позиций'
    get_items_count.admin_order_field = 'items_count'

    def get_total_display(self, obj):
        if hasattr(obj, 'total_price') and obj.total_price is not None:
            return f"{obj.total_price:.2f} руб."
        return "0.00 руб."
    get_total_display.short_description = 'сумма заказа'
    get_total_display.admin_order_field = 'total_price'

    def response_change(self, request, obj):
        next_url = request.GET.get('next')
        if next_url:
            messages.success(request, f'Заказ #{obj.id} успешно обновлен.')
            return redirect(next_url)
        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return super().response_add(request, obj, post_url_continue)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'get_subtotal']
    list_filter = ['order__status']
    list_select_related = ['order', 'product']
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'order', 'product'
        ).annotate(
            subtotal=F('quantity') * F('price')
        )

    def get_subtotal(self, obj):
        if hasattr(obj, 'subtotal') and obj.subtotal is not None:
            return f"{obj.subtotal:.2f} руб."
        return f"{obj.quantity * obj.price:.2f} руб."
    get_subtotal.short_description = 'сумма'
    get_subtotal.admin_order_field = 'subtotal'
