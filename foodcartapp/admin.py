from django.contrib import admin
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django import forms
from django.http import HttpResponseRedirect

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
        ('Общее', {
            'fields': ['name', 'category', 'image', 'get_image_preview', 'price']
        }),
        ('Подробно', {
            'fields': ['special_status', 'description'],
            'classes': ['wide'],
        }),
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

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.all()
        
        if self.instance and self.instance.pk:
            self.fields['product'].disabled = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if instance.product and not instance.price:
            instance.price = instance.product.price
            
        if commit:
            instance.save()
        return instance

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    form = OrderItemForm
    extra = 1
    fields = ['product', 'quantity', 'price']
    readonly_fields = ['price']

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        formset.form.base_fields['product'].widget.can_add_related = True
        formset.form.base_fields['product'].widget.can_change_related = True
        formset.form.base_fields['product'].widget.can_view_related = True
        
        return formset

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'status', 'created_at', 'get_items_count', 'get_total']
    list_filter = ['status', 'created_at', 'payment_method']
    search_fields = ['firstname', 'lastname', 'phonenumber', 'address']
    readonly_fields = ['created_at', 'called_at', 'delivered_at', 'get_total_display']
    inlines = [OrderItemInline]
    list_editable = ['status']
    
    fieldsets = (
        ('Клиент', {
            'fields': ('firstname', 'lastname', 'phonenumber', 'address')
        }),
        ('Заказ', {
            'fields': ('status', 'payment_method', 'comment', 'get_total_display')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'called_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )

    def get_total_display(self, obj):
        return f"{obj.get_total()} руб."
    get_total_display.short_description = 'Общая сумма'

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except Exception as e:
            if 'NOT NULL constraint failed: foodcartapp_orderitem.price' in str(e):
                self.message_user(request, 'Ошибка: цена не была заполнена. Убедитесь, что выбран продукт.', level='error')
                return HttpResponseRedirect(request.path)
            raise

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'get_subtotal']
    list_filter = ['order__status']
    list_select_related = ['order', 'product']
    form = OrderItemForm  # Используем ту же форму
    
    def get_subtotal(self, obj):
        return obj.quantity * obj.price
    get_subtotal.short_description = 'сумма'

    # Автоматическое заполнение цены при сохранении
    def save_model(self, request, obj, form, change):
        if obj.product and not obj.price:
            obj.price = obj.product.price
        super().save_model(request, obj, form, change)