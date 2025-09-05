from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem


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
    
    orders = Order.objects.prefetch_related(
        'items__product'
    ).select_related(
    ).order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    else:
        orders = orders.filter(status__in=['new', 'processing'])
    
    return render(request, template_name='order_items.html', context={
        'orders': orders,
        'status_filter': status_filter
    })