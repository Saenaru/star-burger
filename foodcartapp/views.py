from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.templatetags.static import static
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderItem, Product
from .serializers import ProductSerializer


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.templatetags.static import static
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction

from .models import Order, OrderItem, Product
from .serializers import ProductSerializer

@api_view(['GET'])
def banners_list_api(request):
    # FIXME move data to db?
    data = [
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
    ]
    return Response(data)

@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.select_related('category').available()
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


class RegisterOrderView(APIView):
    @csrf_exempt
    @transaction.atomic
    def post(self, request):
        try:
            order_data = request.data
            
            payment_method = order_data.get('payment_method', 'cash')
            
            valid_payment_methods = ['cash', 'card', 'online']
            if payment_method not in valid_payment_methods:
                payment_method = 'cash'
            
            order = Order.objects.create(
                firstname=order_data.get('firstname', ''),
                lastname=order_data.get('lastname', ''),
                phonenumber=order_data.get('phonenumber', ''),
                address=order_data.get('address', ''),
                payment_method=payment_method,
                status='new'
            )
            
            for item_data in order_data.get('products', []):
                product_id = item_data.get('product')
                quantity = item_data.get('quantity', 1)
                
                try:
                    product = Product.objects.get(id=product_id)
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                except Product.DoesNotExist:
                    return Response(
                        {'status': 'error', 'message': f'Товар с ID {product_id} не найден'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return Response({
                'status': 'success', 
                'message': 'Заказ сохранен',
                'order_id': order.id
            })
            
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

