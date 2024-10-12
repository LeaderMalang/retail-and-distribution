from django.contrib import admin
from .models import Product, Customer, Order, DeliveryRoute, Employee, OrderProduct, Supplier, PurchaseOrder, PurchaseOrderProduct, AccountTransaction, InventoryTransaction

# Inventory Management Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'lot_number', 'expiration_date', 'quantity', 'price')
    search_fields = ('name', 'lot_number')

# Order Management Admin
class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('customer__name',)
    inlines = [OrderProductInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Handle inventory and accounting transactions
        for order_product in OrderProduct.objects.filter(order=obj):
            product = order_product.product
            product.quantity -= order_product.quantity
            product.save()
            InventoryTransaction.objects.create(
                transaction_type='Sale',
                product=product,
                quantity=-order_product.quantity,
                related_order=f"Order #{obj.id}"
            )
        # Record accounting transaction
        total_amount = sum([op.product.price * op.quantity for op in OrderProduct.objects.filter(order=obj)])
        AccountTransaction.objects.create(
            transaction_type='Sale',
            amount=total_amount,
            related_order=f"Order #{obj.id}"
        )

# Purchase Order Management Admin
class PurchaseOrderProductInline(admin.TabularInline):
    model = PurchaseOrderProduct
    extra = 1

class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('supplier__name',)
    inlines = [PurchaseOrderProductInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Handle inventory and accounting transactions
        for purchase_product in PurchaseOrderProduct.objects.filter(purchase_order_id=obj.id):
            product = purchase_product.product
            product.quantity += purchase_product.quantity
            product.save()
            InventoryTransaction.objects.create(
                transaction_type='Purchase',
                product=product,
                quantity=purchase_product.quantity,
                related_order=f"Purchase Order #{obj.id}"
            )
        # Record accounting transaction
        total_amount = sum([pp.product.price * pp.quantity for pp in PurchaseOrderProduct.objects.filter(purchase_order=obj)])
        AccountTransaction.objects.create(
            transaction_type='Purchase',
            amount=total_amount,
            related_order=f"Purchase Order #{obj.id}"
        )

# Account Transaction Admin
class AccountTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'amount', 'date', 'related_order')
    list_filter = ('transaction_type', 'date')
    search_fields = ('related_order',)

# Inventory Transaction Admin
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'product', 'quantity', 'date', 'related_order')
    list_filter = ('transaction_type', 'date')
    search_fields = ('product__name', 'related_order')

# Distribution Planning Admin
class DeliveryRouteAdmin(admin.ModelAdmin):
    list_display = ('order', 'estimated_delivery_time')
    search_fields = ('order__id',)

# HR Management Admin
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'position', 'hire_date', 'salary')
    search_fields = ('first_name', 'last_name', 'position')

# Register models with admin
admin.site.register(Product, ProductAdmin)
admin.site.register(Customer)
admin.site.register(Order, OrderAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(DeliveryRoute, DeliveryRouteAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(AccountTransaction, AccountTransactionAdmin)
admin.site.register(InventoryTransaction, InventoryTransactionAdmin)