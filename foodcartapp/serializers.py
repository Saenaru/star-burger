from rest_framework import serializers
from django.core.validators import MinValueValidator
from .models import Order, OrderItem, Product

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(validators=[MinValueValidator(1)])
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
        extra_kwargs = {
            'firstname': {'required': True},
            'phonenumber': {'required': True},
            'address': {'required': True},
        }
    
    def validate_products(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("Заказ должен содержать хотя бы один товар")
        return value
    
    def validate_phonenumber(self, value):
        if not value.strip():
            raise serializers.ValidationError("Телефон не может быть пустым")
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