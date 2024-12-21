from django.contrib import admin
from .models import Product, Customer, Order, DeliveryRoute, Employee, OrderProduct, Supplier, PurchaseOrder, PurchaseOrderProduct, AccountTransaction, InventoryTransaction, AccountReceivable, AccountPayable, FinancialReport, InventoryBatch, OrderReturn, ProductUnit, DeliveryMan, GeneralLedgerAccount, GeneralLedgerEntry, Payment, OrderReturnProduct, PurchaseOrderReturn, PurchaseOrderReturnProduct, Category, ProductCategory
from django import forms
from django.core.exceptions import ValidationError
from django.contrib import messages

class ProductUnitInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if self.total_form_count() > 1:
            raise ValidationError('You can only add one Product Unit.')

class ProductUnitInline(admin.TabularInline):
    model = ProductUnit
    formset = ProductUnitInlineFormset
    extra = 0

# Inventory Management Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'lot_number', 'stock_quantity')
    search_fields = ('name', 'lot_number')
    readonly_fields = ('stock_quantity', 'total_base_unit_quantity',)
    inlines = [ProductUnitInline]

# Order Management Admin
class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1

class OrderReturnProductInline(admin.TabularInline):
    model = OrderReturnProduct
    extra = 1

class OrderReturnAdmin(admin.ModelAdmin):
    # list_display = ('id', 'customer', 'order_date', 'status')
    # list_filter = ('status', 'order_date')
    # search_fields = ('customer__name',)
    # readonly_fields = ('pending_amount', 'payment_status')
    inlines = [OrderReturnProductInline]

class PurchaseOrderReturnProductInline(admin.TabularInline):
    model = PurchaseOrderReturnProduct
    extra = 1

class PurchaseOrderReturnAdmin(admin.ModelAdmin):
    # list_display = ('id', 'customer', 'order_date', 'status')
    # list_filter = ('status', 'order_date')
    # search_fields = ('customer__name',)
    # readonly_fields = ('pending_amount', 'payment_status')
    inlines = [PurchaseOrderReturnProductInline]

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('customer__name',)
    readonly_fields = ('pending_amount', 'payment_status')
    inlines = [OrderProductInline]

# Purchase Order Management Admin
class PurchaseOrderProductInline(admin.TabularInline):
    model = PurchaseOrderProduct
    extra = 1

class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('supplier__name',)
    readonly_fields = ('pending_amount',)
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
admin.site.register(Category)
admin.site.register(ProductCategory)
admin.site.register(Supplier)
admin.site.register(GeneralLedgerAccount)
admin.site.register(GeneralLedgerEntry)
admin.site.register(Payment)
admin.site.register(Customer)
admin.site.register(DeliveryMan)
admin.site.register(InventoryBatch, InventoryBatchAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PurchaseOrderReturn, PurchaseOrderReturnAdmin)
admin.site.register(OrderReturn, OrderReturnAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(DeliveryRoute, DeliveryRouteAdmin)
admin.site.register(Employee, EmployeeAdmin)
# admin.site.register(AccountTransaction, AccountTransactionAdmin)
admin.site.register(InventoryTransaction, InventoryTransactionAdmin)