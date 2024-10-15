from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from configuration.models import *

# Inventory Management
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    lot_number = models.CharField(max_length=50)
    stock_quantity = models.IntegerField(default=0)
    on_backorder = models.BooleanField(default=False)

    def __str__(self):
        return self.name

# Accounts Management
class GeneralLedger(models.Model):
    account_name = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.account_name} - Balance: {self.balance}"

class AccountReceivable(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"AR for {self.customer.name} - Amount Due: {self.amount_due}"

class AccountPayable(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"AP for {self.supplier.name} - Amount Due: {self.amount_due}"

class FinancialReport(models.Model):
    report_type = models.CharField(max_length=255)
    generated_date = models.DateField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return f"{self.report_type} Report generated on {self.generated_date}"

# Order Management
class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    booking_man = models.ForeignKey(BookingMan, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderProduct')
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered')])

    def __str__(self):
        return f"Order #{self.id} by {self.customer.name}"

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    
    def clean(self):
        if self.product.stock_quantity < self.quantity:
            if not self.product.on_backorder:
                raise ValidationError(
                    f"Quantity '{self.quantity}' exceeds available stock '{self.product.stock_quantity}' for product '{self.product.name}'."
                )
            
        elif self.product.stock_quantity == 0 and not self.product.on_backorder:
            raise ValidationError(
                f"No stock available for product '{self.product.name}'."
            )

    def save(self, *args, **kwargs):
        self.clean()

        if not self.pk:
            product = self.product
            product.stock_quantity -= self.quantity
            product.save()
            InventoryTransaction.objects.create(
                transaction_type='Sale',
                product=self.product,
                quantity=self.quantity,
                related_order=f"Sale Order #{self.order.id}",
            )

            purchase_order_product = PurchaseOrderProduct.objects.filter(product=self.product, quantity__gt=0).first()

            total_amount = purchase_order_product.price * self.quantity

            AccountTransaction.objects.create(
                transaction_type='Sale',
                amount=total_amount,
                related_order=f"Sale Order #{self.order.id}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in Order #{self.order.id}"

# Purchase Order Management

class PurchaseOrder(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='PurchaseOrderProduct')
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Received', 'Received')])

    def __str__(self):
        return f"Purchase Order #{self.id} from {self.supplier.name}"

class PurchaseOrderProduct(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in Purchase Order #{self.purchase_order.id}"

class InventoryBatch(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=50)
    expiration_date = models.DateField()
    quantity = models.IntegerField()

    def __str__(self):
        return f"Batch {self.batch_number} of {self.product.name}"

    def clean(self):
        try:
            purchase_order_product = PurchaseOrderProduct.objects.get(
                purchase_order=self.purchase_order, product=self.product
            )
        except PurchaseOrderProduct.DoesNotExist:
            raise ValidationError(f"Purchase order for product '{self.product.name}' does not exist.")

        total_existing_batches = InventoryBatch.objects.filter(
            purchase_order=self.purchase_order, product=self.product
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0

        total_quantity_after_new_batch = total_existing_batches + self.quantity

        if total_quantity_after_new_batch > purchase_order_product.quantity:
            raise ValidationError(f"Total batch quantity ({total_quantity_after_new_batch}) cannot exceed the "
                                  f"ordered quantity ({purchase_order_product.quantity}) in the purchase order.")

    def save(self, *args, **kwargs):
        self.clean()

        if not self.pk:
            product = self.product
            product.stock_quantity += self.quantity
            product.save()
            InventoryTransaction.objects.create(
                transaction_type='Purchase',
                product=self.product,
                quantity=self.quantity,
                related_order=f"Purchase Order #{self.purchase_order.id}",
            )

            purchase_order_product = PurchaseOrderProduct.objects.get(
                purchase_order=self.purchase_order, product=self.product
            )

            total_amount = purchase_order_product.price * self.quantity

            AccountTransaction.objects.create(
                transaction_type='Purchase',
                amount=total_amount,
                related_order=f"Purchase Order #{self.purchase_order.id}"
            )

        super().save(*args, **kwargs)

# Account Transactions
class AccountTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('Sale', 'Sale'),
        ('Purchase', 'Purchase')
    ]
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    related_order = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type} Transaction - Amount: {self.amount}"

# Inventory Transactions
class InventoryTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('Sale', 'Sale'),
        ('Purchase', 'Purchase')
    ]
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    related_order = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type} Transaction - {self.product.name} (x{self.quantity})"

# HR Management
class Employee(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Distribution Planning
class DeliveryRoute(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    route_details = models.TextField()
    estimated_delivery_time = models.DateTimeField()

    def __str__(self):
        return f"Route for Order #{self.order.id}"