from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from coordinates.utils import calculate_distance, batch_get_coordinates


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = Restaurant.objects.order_by('name')
    products = Product.objects.prefetch_related(
        'menu_items__restaurant'
    ).select_related('category')

    restaurant_ids = [restaurant.id for restaurant in restaurants]
    availability_dict = {}
    menu_items = RestaurantMenuItem.objects.filter(
        restaurant_id__in=restaurant_ids
    ).select_related('restaurant', 'product')
    for item in menu_items:
        key = (item.product_id, item.restaurant_id)
        availability_dict[key] = item.availability
    products_with_restaurant_availability = []
    for product in products:
        ordered_availability = [
            availability_dict.get((product.id, restaurant.id), False)
            for restaurant in restaurants
        ]
        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )
    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    restaurants = Restaurant.objects.all()
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    orders = Order.objects.with_total_price().prefetch_related(
        'items__product',
        'assigned_restaurant'
    ).order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    else:
        orders = orders.filter(status__in=['new', 'processing', 'cooking', 'delivering'])
    if search_query:
        orders = orders.filter(
            Q(firstname__icontains=search_query) |
            Q(lastname__icontains=search_query) |
            Q(phonenumber__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(comment__icontains=search_query) |
            Q(items__product__name__icontains=search_query)
        ).distinct()
    all_addresses = set()
    for order in orders:
        all_addresses.add(order.address)
    all_restaurants = list(Restaurant.objects.all())
    restaurant_addresses = {restaurant.address for restaurant in all_restaurants if restaurant.address}
    all_addresses.update(restaurant_addresses)
    coordinates_cache = batch_get_coordinates(list(all_addresses))
    orders_with_restaurants = []
    for order in orders:
        available_restaurants_with_distance = []
        assigned_restaurant_distance = None
        order_coords = coordinates_cache.get(order.address)
        if order.assigned_restaurant and order.assigned_restaurant.address:
            restaurant_coords = coordinates_cache.get(order.assigned_restaurant.address)
            assigned_restaurant_distance = calculate_distance(order_coords, restaurant_coords)
        if order.status == 'new' and not order.assigned_restaurant and order_coords:
            available_restaurants = order.get_available_restaurants()
            for restaurant in available_restaurants:
                if restaurant.address:
                    restaurant_coords = coordinates_cache.get(restaurant.address)
                    distance = calculate_distance(order_coords, restaurant_coords)
                    available_restaurants_with_distance.append({
                        'restaurant': restaurant,
                        'distance': distance
                    })
            available_restaurants_with_distance.sort(
                key=lambda x: (x['distance'] is None, x['distance'])
            )
        orders_with_restaurants.append({
            'order': order,
            'available_restaurants': available_restaurants_with_distance,
            'assigned_restaurant_distance': assigned_restaurant_distance
        })
    return render(request, template_name='order_items.html', context={
        'orders_with_restaurants': orders_with_restaurants,
        'status_filter': status_filter,
        'search_query': search_query,
        'order_status_choices': Order.STATUS_CHOICES
    })
