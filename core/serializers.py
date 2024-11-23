from rest_framework import serializers
from .models import Order, OrderProduct, Product, Customer
from django.db import transaction

class OrderedProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    products = OrderedProductSerializer(many=True)

    class Meta:
        model = Order
        fields = ['customer', 'booking_man', 'area', 'delivery_man', 'city', 'total_amount', 'pending_amount', 'status', 'payment_status', 'products']

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        
        # Using a transaction to ensure atomicity
        with transaction.atomic():
            # Create the order instance
            order = Order.objects.create(**validated_data)
        
            # Create ordered products for each item in the order
            for product_data in products_data:
                product = Product.objects.get(id=product_data['product'])
                OrderProduct.objects.create(order=order, product=product, quantity=product_data['quantity'], price=product.price)
        
        return order
