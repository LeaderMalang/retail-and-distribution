from django.shortcuts import render, redirect
from .forms import OrderForm, OrderProductFormSet
from .models import *
from .serializers import *
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import OrderSerializer
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse

def create_order_with_products(request):
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        formset = OrderProductFormSet(request.POST, queryset=OrderProduct.objects.none())

        if order_form.is_valid() and formset.is_valid():
            order = order_form.save()

            for form in formset:
                if form.cleaned_data:
                    order_product = form.save(commit=False)
                    order_product.order = order
                    order_product.save()

            return redirect('order_list')

    else:
        order_form = OrderForm()
        formset = OrderProductFormSet(queryset=OrderProduct.objects.none())

    return render(request, 'create_order_with_products.html', {
        'order_form': order_form,
        'formset': formset,
    })


def order_list(request):
    orders = Order.objects.all()
    return render(request, 'order_list.html', {'orders':orders})

def create_order(request):
    customers = Customer.objects.all()
    booking_mans = BookingMan.objects.all()
    citys = City.objects.all()
    areas = Area.objects.all()
    delivery_mans = DeliveryMan.objects.all()
    products = Product.objects.all()


    return render(request, 'create_order.html', {'customers':customers, 'booking_mans':booking_mans, 'areas':areas, 'delivery_mans':delivery_mans, 'citys':citys, 'products': products})

@csrf_exempt
def create_api_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        try:
            customer = Customer.objects.get(id=data['customer'])
            booking_man = BookingMan.objects.get(id=data['booking_man'])
            delivery_man = DeliveryMan.objects.get(id=data['delivery_man'])
            city = City.objects.get(id=data['city'])
            area = Area.objects.get(id=data['area'])
            
            order = Order.objects.create(
                customer=customer,
                booking_man=booking_man,
                delivery_man=delivery_man,
                city=city,
                area=area,
                total_amount=int(data['total_amount']),
                pending_amount=int(data['pending_amount']),
                status=data['status'],
                payment_status=data['payment_status'],
            )

            for product_data in data['products']:
                product = Product.objects.get(id=product_data['product'])
                
                OrderProduct.objects.create(order=order, product=product, quantity=int(product_data['quantity']))

            return JsonResponse({'order_id': order.id, 'status': 'success'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)
