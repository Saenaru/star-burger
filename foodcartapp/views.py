from django.http import JsonResponse
from django.templatetags.static import static
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction

from .models import Order, OrderItem, Product


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


@csrf_exempt
@transaction.atomic
def register_order(request):
    if request.method == 'POST':
        try:
            order_data = json.loads(request.body)
            
            order = Order.objects.create(
                firstname=order_data.get('firstname', ''),
                lastname=order_data.get('lastname', ''),
                phonenumber=order_data.get('phonenumber', ''),
                address=order_data.get('address', ''),
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
                    raise Exception(f"Товар с ID {product_id} не найден")
            
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
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Заказ сохранен',
                'order_id': order.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Неверный JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Метод не разрешен'}, status=405)