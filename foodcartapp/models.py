from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Sum, F, Count, Prefetch
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from collections import defaultdict


class Restaurant(models.Model):
    name = models.CharField('название', max_length=50)
    address = models.CharField('адрес', max_length=100, blank=True)
    contact_phone = models.CharField('контактный телефон', max_length=50, blank=True)

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField('название', max_length=50)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('название', max_length=50)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(1)]
    )
    image = models.ImageField('картинка')
    special_status = models.BooleanField('спец.предложение', default=False, db_index=True)
    description = models.TextField('описание', max_length=200, blank=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField('в продаже', default=True, db_index=True)

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [['restaurant', 'product']]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_total_price(self):
        return self.annotate(
            total_price=Sum(F('items__quantity') * F('items__price'))
        )

    def with_items_count(self):
        return self.annotate(
            items_count=Count('items')
        )


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('cooking', 'Готовится'),
        ('delivering', 'Доставляется'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменен'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличными'),
        ('card', 'Картой'),
        ('online', 'Онлайн'),
    ]

    firstname = models.CharField('имя', max_length=50)
    lastname = models.CharField('фамилия', max_length=50, blank=True)
    phonenumber = PhoneNumberField('телефон', db_index=True)
    address = models.CharField('адрес', max_length=200)
    status = models.CharField(
        'статус', 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='new', 
        db_index=True
    )
    comment = models.TextField('комментарий', blank=True)
    created_at = models.DateTimeField('создан', auto_now_add=True, db_index=True)
    called_at = models.DateTimeField('звонок', blank=True, null=True, db_index=True, editable=True)
    delivered_at = models.DateTimeField('доставлен', blank=True, null=True, db_index=True, editable=True)
    payment_method = models.CharField(
        'способ оплаты',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        db_index=True
    )
    assigned_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='ресторан для приготовления',
        related_name='assigned_orders',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['phonenumber']),
            models.Index(fields=['lastname', 'firstname']),
            models.Index(fields=['address']),
            models.Index(fields=['created_at']),
            models.Index(fields=['called_at']),
            models.Index(fields=['delivered_at']),
            models.Index(fields=['payment_method']),
        ]

    def get_available_restaurants(self):
        order_items = self.items.select_related('product').all()
        order_product_ids = [item.product_id for item in order_items]
        if not order_product_ids:
            return Restaurant.objects.none()
        restaurant_menu_items = RestaurantMenuItem.objects.filter(
            availability=True,
            product_id__in=order_product_ids
        ).select_related('restaurant', 'product')
        restaurant_products = defaultdict(set)
        for menu_item in restaurant_menu_items:
            restaurant_products[menu_item.restaurant].add(menu_item.product_id)
        available_restaurants = []
        order_product_set = set(order_product_ids)
        for restaurant, products in restaurant_products.items():
            if order_product_set.issubset(products):
                available_restaurants.append(restaurant)
        return available_restaurants

    def __str__(self):
        return f"Заказ #{self.id} от {self.firstname} {self.lastname}"

    def get_total(self):
        """Возвращает общую сумму заказа"""
        if hasattr(self, 'total_price'):
            return self.total_price
        return self.items.aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0
    
    get_total.short_description = 'сумма заказа'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='заказ'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='товар'
    )
    quantity = models.PositiveIntegerField(
        'количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'
        unique_together = ['order', 'product']

    def __str__(self):
        return f"{self.product.name} x{self.quantity} в заказе #{self.order.id}"

    def get_cost(self):
        """Возвращает стоимость позиции (количество * цена)"""
        return self.quantity * self.price
    
    get_cost.short_description = 'стоимость позиции'