from django.shortcuts import render, redirect
from .forms import OrderForm, OrderProductFormSet
from .models import *
from .serializers import *
from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import OrderSerializer
from django.views.decorators.http import require_http_methods
import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

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

def update_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order_products = order.order_products.all()

    print(f'order_products: {order_products}')

    ordered_product_ids = [order_product.product.id for order_product in order_products]

    print(f'ordered_product_ids: {ordered_product_ids}')
    customers = Customer.objects.all()
    booking_mans = BookingMan.objects.all()
    citys = City.objects.all()
    areas = Area.objects.all()
    delivery_mans = DeliveryMan.objects.all()
    products = Product.objects.all()

    return render(request, 'update_order.html', {'customers':customers, 'booking_mans':booking_mans, 'areas':areas, 'delivery_mans':delivery_mans, 'citys':citys, 'products': products, 'order':order, 'order_products':order_products, 'ordered_product_ids':ordered_product_ids})

def delete_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    order_products = OrderProduct.objects.filter(order=order)

    for order_product in order_products:
        product = order_product.product
        product.stock_quantity += order_product.quantity
        product.save()
        order_product.delete()

    GeneralLedgerEntry.objects.filter(
            description__icontains=f"Order #{order.id}"
        ).delete()

    Payment.objects.filter(
            content_type=ContentType.objects.get_for_model(Order),
            object_id=order.id
        ).delete()

    order.delete()

    return redirect('/order_list/')

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

@csrf_exempt
@require_http_methods(["PUT"])
def update_api_order(request, order_id):
    try:
        data = json.loads(request.body)

        # Fetch the order object or return an error
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)

        # Update order fields from the payload
        order.customer = Customer.objects.get(id=data['customer'])
        order.booking_man = BookingMan.objects.get(id=data['booking_man'])
        order.delivery_man = DeliveryMan.objects.get(id=data['delivery_man'])
        order.city = City.objects.get(id=data['city'])
        order.area = Area.objects.get(id=data['area'])
        order.total_amount = Decimal(data['total_amount'])
        order.paid_amount = Decimal(data.get('paid_amount', order.paid_amount))
        order.status = data['status']
        order.payment_status = data['payment_status']  # This may get recalculated in save()

        # Save the order to calculate pending amount and record ledger entries
        order.save()

        # Handle product updates in the order
        product_ids_in_payload = {item['product'] for item in data['products']}
        existing_order_products = OrderProduct.objects.filter(order=order)

        for product_data in data['products']:
            product = Product.objects.get(id=product_data['product'])
            quantity = int(product_data['quantity'])

            # Get or create the OrderProduct instance
            order_product, created = OrderProduct.objects.get_or_create(order=order, product=product)

            if created:
                # New product - decrease the stock and set the quantity
                product.stock_quantity -= quantity
                product.save()
                order_product.quantity = quantity
                order_product.save()
            else:
                # Update quantity and handle stock adjustments
                if order_product.quantity != quantity:
                    # Revert previous stock adjustment (increase stock for previous quantity)
                    product.stock_quantity += order_product.quantity
                    product.save()

                    # Update to the new quantity and decrease stock for the new quantity
                    product.stock_quantity -= quantity
                    product.save()

                    order_product.quantity = quantity
                    order_product.save()

        # Remove products no longer in the updated payload (increase stock when removed)
        products_to_remove = existing_order_products.exclude(product_id__in=product_ids_in_payload)
        for order_product in products_to_remove:
            product = order_product.product
            product.stock_quantity += order_product.quantity  # Increase stock quantity
            product.save()

            # Delete the order product
            order_product.delete()

        # Record general ledger entries
        order.record_general_ledger_entries()

        # Prepare response data
        order_products = OrderProduct.objects.filter(order=order).select_related('product')
        products_list = [
            {
                "product_id": order_product.product.id,
                "product_name": order_product.product.name,
                "quantity": order_product.quantity,
            }
            for order_product in order_products
        ]

        return JsonResponse({
            'order_id': order.id,
            'status': 'updated',
            'payment_status': order.payment_status,
            'pending_amount': str(order.pending_amount),
            'products': products_list
        })

    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def delete_api_order(request, order_id):
    try:
        # Fetch the order object or raise a 404 error
        order = get_object_or_404(Order, id=order_id)

        # Revert stock for associated products
        order_products = OrderProduct.objects.filter(order=order)
        for order_product in order_products:
            product = order_product.product
            product.stock_quantity += order_product.quantity
            product.save()
            order_product.delete()

        GeneralLedgerEntry.objects.filter(
            description__icontains=f"Order #{order.id}"
        ).delete()

        Payment.objects.filter(
            content_type=ContentType.objects.get_for_model(Order),
            object_id=order.id
        ).delete()

        order.delete()

        return redirect('/order_list/')

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=400)

@csrf_exempt
@require_http_methods(["POST"])
def create_api_purchase_order(request):
    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['supplier', 'products', 'status', 'paid_amount']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f"{field} is required."}, status=400)

        # Fetch supplier
        try:
            supplier = Supplier.objects.get(id=data['supplier'])
        except Supplier.DoesNotExist:
            return JsonResponse({'error': 'Supplier not found.'}, status=404)

        # Create the purchase order
        purchase_order = PurchaseOrder(
            supplier=supplier,
            status=data['status'],
            paid_amount=Decimal(data['paid_amount']),
        )
        purchase_order.save()

        # Process products
        total_amount = Decimal(0)
        for product_data in data['products']:
            product_id = product_data['product']
            quantity = product_data['quantity']
            price = Decimal(product_data['price'])

            # Fetch product
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'error': f"Product with ID {product_id} not found."}, status=404)

            # Create PurchaseOrderProduct entry
            PurchaseOrderProduct.objects.create(
                purchase_order=purchase_order,
                product=product,
                quantity=quantity,
                price=price
            )

            # Calculate total amount
            total_amount += price * quantity

        # Update purchase order totals
        purchase_order.total_amount = total_amount
        purchase_order.calculate_total_amount()
        purchase_order.save()

        # Prepare response data
        products_list = [
            {
                "product_id": product_data['product'],
                "quantity": product_data['quantity'],
                "price": str(product_data['price']),
            }
            for product_data in data['products']
        ]

        return JsonResponse({
            'status': 'success',
            'purchase_order_id': purchase_order.id,
            'total_amount': str(purchase_order.total_amount),
            'paid_amount': str(purchase_order.paid_amount),
            'pending_amount': str(purchase_order.pending_amount),
            'payment_status': purchase_order.payment_status,
            'products': products_list
        })

    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["PUT"])
def update_api_purchase_order(request, order_id):
    try:
        data = json.loads(request.body)

        # Fetch the existing purchase order
        try:
            purchase_order = PurchaseOrder.objects.get(id=order_id)
        except PurchaseOrder.DoesNotExist:
            return JsonResponse({'error': 'Purchase Order not found'}, status=404)

        # Update basic details
        purchase_order.status = data.get('status', purchase_order.status)
        purchase_order.paid_amount = Decimal(data.get('paid_amount', purchase_order.paid_amount))

        # Recalculate pending amount
        purchase_order.calculate_total_amount()

        # Process products
        total_amount = Decimal(0)
        existing_products = {product.product.id for product in purchase_order.purchase_order_products.all()}
        product_ids_in_payload = {product_data['product'] for product_data in data['products']}

        # Handle product updates and additions
        for product_data in data['products']:
            product_id = product_data['product']
            quantity = product_data['quantity']
            price = Decimal(product_data['price'])

            # Fetch product
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'error': f"Product with ID {product_id} not found."}, status=404)

            # Get or create PurchaseOrderProduct entry
            order_product, created = PurchaseOrderProduct.objects.get_or_create(
                purchase_order=purchase_order, product=product)

            # Update or add product quantity and price
            order_product.quantity = quantity
            order_product.price = price
            order_product.save()

            total_amount += price * quantity

        # Remove products no longer in the updated payload
        products_to_remove = purchase_order.purchase_order_products.exclude(
            product_id__in=product_ids_in_payload)
        for order_product in products_to_remove:
            order_product.delete()

        # Update the total amount of the purchase order
        purchase_order.total_amount = total_amount
        purchase_order.calculate_total_amount()
        purchase_order.save()

        # If there is a payment made, record the payment and adjust the ledger
        if purchase_order.paid_amount > 0:
            purchase_order.record_payment(purchase_order.paid_amount)

        # Prepare the response
        products_list = [
            {
                "product_id": order_product.product.id,
                "quantity": order_product.quantity,
                "price": str(order_product.price),
            }
            for order_product in purchase_order.purchase_order_products.all()
        ]

        return JsonResponse({
            'status': 'success',
            'purchase_order_id': purchase_order.id,
            'total_amount': str(purchase_order.total_amount),
            'paid_amount': str(purchase_order.paid_amount),
            'pending_amount': str(purchase_order.pending_amount),
            'payment_status': purchase_order.payment_status,
            'products': products_list
        })

    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_api_purchase_order(request, order_id):
    try:
        # Fetch the purchase order
        try:
            purchase_order = PurchaseOrder.objects.get(id=order_id)
        except PurchaseOrder.DoesNotExist:
            return JsonResponse({'error': 'Purchase Order not found'}, status=404)

        # Record a general ledger entry for the deletion
        general_ledger_description = f"Purchase Order #{purchase_order.id} deleted"
        cash_account, _ = GeneralLedgerAccount.objects.get_or_create(name='Cash', defaults={'code': 'CE'})
        accounts_payable, _ = GeneralLedgerAccount.objects.get_or_create(name='Accounts Payable', defaults={'code': 'AP'})

        GeneralLedgerEntry.objects.create(
            account=cash_account,
            date=timezone.now(),
            description=general_ledger_description,
            debit=0,
            credit=purchase_order.paid_amount
        )

        GeneralLedgerEntry.objects.create(
            account=accounts_payable,
            date=timezone.now(),
            description=general_ledger_description,
            debit=purchase_order.paid_amount,
            credit=0
        )

        # Delete the related products
        purchase_order.purchase_order_products.all().delete()

        # Delete the payment record
        content_type = ContentType.objects.get_for_model(purchase_order)
        Payment.objects.filter(content_type=content_type, object_id=purchase_order.id).delete()

        # Delete the purchase order
        purchase_order.delete()

        return JsonResponse({'status': 'success', 'message': f'Purchase Order #{order_id} deleted.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

