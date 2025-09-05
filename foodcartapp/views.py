from django.http import JsonResponse
from django.templatetags.static import static
import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from .models import Order, OrderItem, Product
from .serializers import OrderSerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class RegisterOrderView(APIView):
    @transaction.atomic
    def post(self, request):
        try:
            serializer = OrderSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            order = serializer.save()
            
            self._log_order(order)
            
            return Response({
                'status': 'success', 
                'message': 'Заказ сохранен',
                'order_id': order.id
            }, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            return Response({
                'status': 'error',
                'message': 'Ошибка валидации данных',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(f"Неожиданная ошибка при создании заказа: {e}")
            return Response({
                'status': 'error',
                'message': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _log_order(self, order):
        print("=" * 50)
        print(f"СОХРАНЕН ЗАКАЗ #{order.id}")
        print(f"Имя: {order.firstname}")
        print(f"Фамилия: {order.lastname}")
        print(f"Телефон: {order.phonenumber}")
        print(f"Адрес: {order.address}")
        print(f"Статус: {order.get_status_display()}")
        print("Товары:")
        
        for item in order.items.all():
            print(f"  - {item.product.name}: {item.quantity} x {item.price} = {item.quantity * item.price}")
        
        print(f"Итого: {order.get_total()}")
        print("=" * 50)