from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from django.core.validators import MinValueValidator
from .models import Order, OrderItem, Product

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        error_messages={
            'does_not_exist': 'Продукт с ID "{pk_value}" не существует',
            'incorrect_type': 'ID продукта должно быть числом'
        }
    )
    quantity = serializers.IntegerField(
        validators=[MinValueValidator(1)],
        error_messages={
            'min_value': 'Количество не может быть меньше 1',
            'invalid': 'Количество должно быть числом'
        }
    )
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, write_only=True)
    phonenumber = PhoneNumberField(
        error_messages={
            'blank': 'Телефон не может быть пустым',
            'invalid': 'Введен некорректный номер телефона'
        }
    )
    firstname = serializers.CharField(
        error_messages={
            'blank': 'Имя не может быть пустым',
            'invalid': 'Имя должно быть строкой'
        }
    )
    lastname = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(
        error_messages={
            'blank': 'Адрес не может быть пустым'
        }
    )
    
    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
    
    def validate_products(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("Заказ должен содержать хотя бы один товар")
        return value
    
    def validate(self, data):
        products_data = data.get('products', [])
        
        for product_data in products_data:
            product = product_data['product']
            quantity = product_data['quantity']
            
            if not product.menu_items.filter(availability=True).exists():
                raise serializers.ValidationError(
                    f"Продукт '{product.name}' недоступен для заказа"
                )
            
            if quantity > 100:
                raise serializers.ValidationError(
                    f"Слишком большое количество для продукта '{product.name}'"
                )
        
        return data
    
    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        
        for product_data in products_data:
            product = product_data['product']
            quantity = product_data['quantity']
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )
        
        return order
    
class OrderOutputSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, read_only=True, source='items')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total = serializers.DecimalField(source='get_total', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'firstname', 'lastname', 'phonenumber', 'address', 
            'status', 'status_display', 'comment', 'created_at',
            'payment_method', 'products', 'total'
        ]
        read_only_fields = fields