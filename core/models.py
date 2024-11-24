from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from configuration.models import *
from django.utils import timezone        
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Supplier(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    contact_info = models.TextField()

    def __str__(self):
        return self.name


# Inventory Management
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    lot_number = models.CharField(max_length=50)
    stock_quantity = models.IntegerField(default=0)
    total_base_unit_quantity = models.IntegerField(default=0)
    on_backorder = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class ProductUnit(models.Model):
    UNIT_CHOICES = [
        ('box', 'Box'),
        ('tablet', 'Tablet'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_name = models.CharField(max_length=50, choices=UNIT_CHOICES)
    quantity_in_base_unit = models.IntegerField()

    def __str__(self):
        return f"{self.unit_name} of {self.product.name} ({self.quantity_in_base_unit} per {self.unit_name})"

# Accounts Management

class AccountReceivable(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    # paid_amount
    # paid_date
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"AR for {self.customer.name} - Amount Due: {self.amount_due}"


class AccountPayable(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    # paid_amount
    # paid_date
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

class DeliveryMan(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class GeneralLedgerAccount(models.Model):
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class GeneralLedgerEntry(models.Model):
    account = models.ForeignKey(GeneralLedgerAccount, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.date} - {self.description}"

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    booking_man = models.ForeignKey(BookingMan, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    delivery_man = models.ForeignKey(DeliveryMan, on_delete=models.CASCADE, null=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderProduct')
    order_date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=50, choices=[('PAID', 'PAID'), ('PARTIALLY PAID', 'PARTIALLY PAID')], null=True)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Returned', 'Returned')])

    def __str__(self):
        return f"Order #{self.id} by {self.customer.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the order first

        self.pending_amount = self.total_amount - self.paid_amount

        self.record_general_ledger_entries()

        super().save(*args, **kwargs)
    
    def record_general_ledger_entries(self):
        accounts_receivable, _ = GeneralLedgerAccount.objects.get_or_create(
        name='Accounts Receivable', 
        defaults={'code': 'AR'}
    )
        revenue_account, _ = GeneralLedgerAccount.objects.get_or_create(
        name='Revenue', 
        defaults={'code': 'RE'}  # Assuming 'RE' is the code for Revenue
    )

        GeneralLedgerEntry.objects.create(
            account=accounts_receivable,
            date=timezone.now(),
            description=f"Order #{self.id} - Sale to {self.customer}",
            debit=self.total_amount,
            credit=0
        )

        GeneralLedgerEntry.objects.create(
            account=revenue_account,
            date=timezone.now(),
            description=f"Order #{self.id} - Sale revenue",
            debit=0,
            credit=self.total_amount
        )
        amount_paid = self.paid_amount

        self.record_payment(amount_paid)

    def record_payment(self, amount_paid):
        cash_account, _ = GeneralLedgerAccount.objects.get_or_create(
        name='Cash', 
        defaults={'code': 'CE'}
    )
        accounts_receivable, _ = GeneralLedgerAccount.objects.get_or_create(
        name='Accounts Receivable', 
        defaults={'code': 'AR'}
    )

        GeneralLedgerEntry.objects.create(
            account=cash_account,
            date=timezone.now(),
            description=f"Payment received for Order #{self.id}",
            debit=amount_paid,
            credit=0
        )

        GeneralLedgerEntry.objects.create(
            account=accounts_receivable,
            date=timezone.now(),
            description=f"Reduce Accounts Receivable for Order #{self.id}",
            debit=0,
            credit=amount_paid
        )

        content_type = ContentType.objects.get_for_model(self)

        Payment.objects.create(
            content_type=content_type,
            object_id=self.id,
            amount_paid=amount_paid
        )

        if self.pending_amount <= 0:
            self.payment_status = 'PAID'
            self.pending_amount = 0
        else:
            self.payment_status = 'PARTIALLY PAID'

class Payment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    order = GenericForeignKey('content_type', 'object_id')
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount_paid} for {self.order}"

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    
    def clean(self):
        if not self.pk:
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
            product_unit = ProductUnit.objects.get(product=product)
            if product_unit and product_unit.quantity_in_base_unit:
                product.total_base_unit_quantity = product_unit.quantity_in_base_unit*product.stock_quantity
                product.save()
            
            InventoryTransaction.objects.create(
                transaction_type='Sale',
                product=self.product,
                quantity=self.quantity,
                related_order=f"Sale Order #{self.order.id}",
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in Order #{self.order.id}"

class OrderReturn(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    return_date = models.DateField(auto_now_add=True)
    total_return_amount = models.DecimalField(max_digits=10, decimal_places=2)
    returned_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_status = models.CharField(
        max_length=50,
        choices=[('REFUNDED', 'REFUNDED'), ('PARTIALLY REFUNDED', 'PARTIALLY REFUNDED')],
        null=True
    )
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Return for Order #{self.order.id} on {self.return_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.record_return_entries()
        super().save(*args, **kwargs)

    def record_return_entries(self):
        accounts_receivable, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Accounts Receivable', defaults={'code': 'AR'}
        )
        revenue_account, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Revenue', defaults={'code': 'RE'}
        )

        GeneralLedgerEntry.objects.create(
            account=revenue_account,
            date=timezone.now(),
            description=f"Return Order #{self.order.id} - Revenue reversal",
            debit=self.total_return_amount,
            credit=0
        )

        GeneralLedgerEntry.objects.create(
            account=accounts_receivable,
            date=timezone.now(),
            description=f"Return Order #{self.order.id} - Reduce Accounts Receivable",
            debit=0,
            credit=self.total_return_amount
        )

        amount_refunded = self.returned_amount
        self.record_refund(amount_refunded)

    def record_refund(self, amount_refunded):
        cash_account, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Cash', defaults={'code': 'CE'}
        )
        accounts_receivable, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Accounts Receivable', defaults={'code': 'AR'}
        )

        GeneralLedgerEntry.objects.create(
            account=cash_account,
            date=timezone.now(),
            description=f"Refund issued for Order #{self.order.id}",
            debit=0,
            credit=amount_refunded
        )

        GeneralLedgerEntry.objects.create(
            account=accounts_receivable,
            date=timezone.now(),
            description=f"Reduce Accounts Receivable due to refund for Order #{self.order.id}",
            debit=amount_refunded,
            credit=0
        )

        content_type = ContentType.objects.get_for_model(self)
        Payment.objects.create(
            content_type=content_type,
            object_id=self.id,
            amount_paid=-amount_refunded
        )

        self.returned_amount -= amount_refunded
        if self.returned_amount <= 0:
            self.refund_status = 'REFUNDED'
            self.returned_amount = 0
        else:
            self.refund_status = 'PARTIALLY REFUNDED'

class OrderReturnProduct(models.Model):
    order_return = models.ForeignKey(OrderReturn, on_delete=models.CASCADE, related_name='returned_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    returned_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.returned_quantity} of {self.product.name} for Return Order #{self.order_return.order.id}"

    def product_in_order(self):
        order_products = self.order_return.order.order_products.all()
        return any(order_product.product_id == self.product_id for order_product in order_products)
    
    def validate_returned_quantity(self):
        order_product = self.order_return.order.order_products.filter(product=self.product).first()
        if order_product and self.returned_quantity > order_product.quantity:
            raise ValidationError(
                f"Returned quantity {self.returned_quantity} exceeds the ordered quantity {order_product.quantity} "
                f"for product '{self.product.name}' in Order #{self.order_return.order.id}"
            )
    
    def clean(self):
        if not self.product_in_order():
            raise ValidationError(f"Product '{self.product.name}' does not belong to Order #{self.order_return.order.id}")
        
        self.validate_returned_quantity()
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.pk:
            product = self.product
            product.stock_quantity += self.returned_quantity
            product.save()

        super().save(*args, **kwargs)

# Purchase Order Management

class PurchaseOrder(models.Model):
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    products = models.ManyToManyField('Product', through='PurchaseOrderProduct')
    order_date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Received', 'Received')])
    payment_status = models.CharField(max_length=50, choices=[('PAID', 'PAID'), ('PARTIALLY PAID', 'PARTIALLY PAID')], null=True)

    def __str__(self):
        return f"Purchase Order #{self.id} from {self.supplier.name}"

    def save(self, *args, **kwargs):
        self.calculate_total_amount()
        super().save(*args, **kwargs)

        if self.paid_amount > 0:
            self.record_payment(self.paid_amount)

    def calculate_total_amount(self):
        # purchase_order_products = self.purchaseorderproduct_set.all()
        # total_amount = sum(p.price * p.quantity for p in purchase_order_products)
        # self.total_amount = total_amount
        self.pending_amount = self.total_amount - self.paid_amount

    def record_payment(self, amount_paid):
        if self._state.adding:
            self.save()

        cash_account, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Cash', defaults={'code': 'CE'}
        )
        accounts_payable, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Accounts Payable', defaults={'code': 'AP'}
        )

        GeneralLedgerEntry.objects.create(
            account=cash_account,
            date=timezone.now(),
            description=f"Payment made for Purchase Order #{self.id}",
            debit=amount_paid,
            credit=0
        )

        GeneralLedgerEntry.objects.create(
            account=accounts_payable,
            date=timezone.now(),
            description=f"Reduce Accounts Payable for Purchase Order #{self.id}",
            debit=0,
            credit=amount_paid
        )

        content_type = ContentType.objects.get_for_model(self)
        Payment.objects.create(
            content_type=content_type,
            object_id=self.id,
            amount_paid=amount_paid
        )

        if self.pending_amount <= 0:
            self.payment_status = 'PAID'
            self.pending_amount = 0
        else:
            self.payment_status = 'PARTIALLY PAID'

        PurchaseOrder.objects.filter(id=self.id).update(
            pending_amount=self.pending_amount, status=self.status
        )

class PurchaseOrderProduct(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='purchase_order_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in Purchase Order #{self.purchase_order.id}"

class PurchaseOrderReturn(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='returns')
    return_date = models.DateField(auto_now_add=True)
    total_return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    returned_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_status = models.CharField(
        max_length=50,
        choices=[('REFUNDED', 'REFUNDED'), ('PARTIALLY REFUNDED', 'PARTIALLY REFUNDED')],
        null=True
    )
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Return for Purchase Order #{self.purchase_order.id} on {self.return_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.calculate_return_amount()
        self.record_return_entries()

    def calculate_return_amount(self):
        self.returned_amount = self.total_return_amount

    def record_return_entries(self):
        cash_account, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Cash', defaults={'code': 'CE'}
        )
        accounts_payable, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Accounts Payable', defaults={'code': 'AP'}
        )

        # Create entries to reverse the purchase order costs
        GeneralLedgerEntry.objects.create(
            account=accounts_payable,
            date=timezone.now(),
            description=f"Return processed for Purchase Order #{self.purchase_order.id}",
            debit=self.total_return_amount,
            credit=0
        )

        GeneralLedgerEntry.objects.create(
            account=cash_account,
            date=timezone.now(),
            description=f"Return amount credited for Purchase Order #{self.purchase_order.id}",
            debit=0,
            credit=self.total_return_amount
        )

        if self.returned_amount > 0:
            self.record_refund(self.returned_amount)

    def record_refund(self, amount_refunded):
        cash_account, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Cash', defaults={'code': 'CE'}
        )
        accounts_payable, _ = GeneralLedgerAccount.objects.get_or_create(
            name='Accounts Payable', defaults={'code': 'AP'}
        )

        GeneralLedgerEntry.objects.create(
            account=cash_account,
            date=timezone.now(),
            description=f"Refund issued for Purchase Order #{self.purchase_order.id}",
            debit=0,
            credit=amount_refunded
        )

        GeneralLedgerEntry.objects.create(
            account=accounts_payable,
            date=timezone.now(),
            description=f"Reduce Accounts Payable due to refund for Purchase Order #{self.purchase_order.id}",
            debit=amount_refunded,
            credit=0
        )

        content_type = ContentType.objects.get_for_model(self)
        Payment.objects.create(
            content_type=content_type,
            object_id=self.id,
            amount_paid=-amount_refunded
        )

        self.returned_amount -= amount_refunded
        if self.returned_amount <= 0:
            self.refund_status = 'REFUNDED'
            self.returned_amount = 0
        else:
            self.refund_status = 'PARTIALLY REFUNDED'

class PurchaseOrderReturnProduct(models.Model):
    purchase_order_return = models.ForeignKey(PurchaseOrderReturn, on_delete=models.CASCADE, related_name='returned_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    returned_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.returned_quantity} of {self.product.name} for Return Order #{self.purchase_order_return.id}"

    def clean(self):
        purchase_order = self.purchase_order_return.purchase_order
        
        valid_products = purchase_order.products.all()

        if self.product not in valid_products:
            raise ValidationError(f"The product {self.product.name} is not part of Purchase Order #{purchase_order.id}.")

        purchase_order_product = PurchaseOrderProduct.objects.filter(purchase_order=purchase_order, product=self.product).first()
        
        if purchase_order_product:
            if self.returned_quantity > purchase_order_product.quantity:
                raise ValidationError(f"You cannot return more than the ordered quantity for {self.product.name}.")

    def save(self, *args, **kwargs):
        self.clean()
        if not self.pk:
            purchase_order_product = PurchaseOrderProduct.objects.get(purchase_order=self.purchase_order_return.purchase_order, product=self.product)
            purchase_order_product.quantity -= self.returned_quantity
            purchase_order_product.save()

        super().save(*args, **kwargs)

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

            product_unit = ProductUnit.objects.get(product=product)
            if product_unit and product_unit.quantity_in_base_unit:
                product.total_base_unit_quantity = product_unit.quantity_in_base_unit*product.stock_quantity
                product.save()

            InventoryTransaction.objects.create(
                transaction_type='Purchase',
                product=self.product,
                quantity=self.quantity,
                related_order=f"Purchase Order #{self.purchase_order.id}",
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