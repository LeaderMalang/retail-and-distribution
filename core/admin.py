from django.contrib import admin
from .models import Product, Customer, Order, DeliveryRoute, Employee, OrderProduct, Supplier, PurchaseOrder, PurchaseOrderProduct, AccountTransaction, InventoryTransaction, GeneralLedger, AccountReceivable, AccountPayable, FinancialReport, InventoryBatch
from django.core.exceptions import ValidationError
from django.contrib import messages

# Inventory Management Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'lot_number', 'stock_quantity')
    search_fields = ('name', 'lot_number')
    readonly_fields = ('stock_quantity',)

# Order Management Admin
class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('customer__name',)
    inlines = [OrderProductInline]

# Purchase Order Management Admin
class PurchaseOrderProductInline(admin.TabularInline):
    model = PurchaseOrderProduct
    extra = 1

class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('supplier__name',)
    inlines = [PurchaseOrderProductInline]

    # def save_formset(self, request, form, formset, change):
    #     instances = formset.save(commit=False)
    #     for instance in instances:
    #         if isinstance(instance, PurchaseOrderProduct):
    #             product = instance.product
    #             product.quantity += instance.quantity
    #             product.save()
    #             InventoryTransaction.objects.create(
    #                 transaction_type='Purchase',
    #                 product=product,
    #                 quantity=instance.quantity,
    #                 related_order=f"Purchase Order #{instance.purchase_order.id}"
    #             )
    #             # Record accounting transaction
    #             total_amount = instance.product.price * instance.quantity
    #             AccountTransaction.objects.create(
    #                 transaction_type='Purchase',
    #                 amount=total_amount,
    #                 related_order=f"Purchase Order #{instance.purchase_order.id}"
    #             )
    #     super().save_formset(request, form, formset, change)

class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'batch_number', 'expiration_date', 'quantity')
    search_fields = ('product__name', 'batch_number')

# Account Management Admin
class GeneralLedgerAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'balance')
    search_fields = ('account_name',)

class AccountReceivableAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount_due', 'due_date')
    search_fields = ('customer__name',)

class AccountPayableAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'amount_due', 'due_date')
    search_fields = ('supplier__name',)

class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_date')
    search_fields = ('report_type',)

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
admin.site.register(InventoryBatch, InventoryBatchAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(DeliveryRoute, DeliveryRouteAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(AccountTransaction, AccountTransactionAdmin)
admin.site.register(InventoryTransaction, InventoryTransactionAdmin)