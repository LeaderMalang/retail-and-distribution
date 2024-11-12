from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from configuration.models import *
from django.utils import timezone



class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sync_status=models.BooleanField(default=False)

    class Meta:
        abstract = True

class Supplier(TimeStampMixin):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    contact_info = models.TextField()
    

    def __str__(self):
        return self.name


# Inventory Management
class Product(TimeStampMixin):
    name = models.CharField(max_length=255)
    description = models.TextField()
    lot_number = models.CharField(max_length=50)
    stock_quantity = models.IntegerField(default=0)
    total_base_unit_quantity = models.IntegerField(default=0)
    on_backorder = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class ProductUnit(TimeStampMixin):
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

class AccountReceivable(TimeStampMixin):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    # paid_amount
    # paid_date
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"AR for {self.customer.name} - Amount Due: {self.amount_due}"


class AccountPayable(TimeStampMixin):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    # paid_amount
    # paid_date
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"AP for {self.supplier.name} - Amount Due: {self.amount_due}"

class FinancialReport(TimeStampMixin):
    report_type = models.CharField(max_length=255)
    generated_date = models.DateField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return f"{self.report_type} Report generated on {self.generated_date}"

# Order Management
class Customer(TimeStampMixin):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    city = models.ForeignKey(City,null=True, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, null=True,on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class DeliveryMan(TimeStampMixin):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class GeneralLedgerAccount(TimeStampMixin):
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

class GeneralLedgerEntry(TimeStampMixin):
    account = models.ForeignKey(GeneralLedgerAccount, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.date} - {self.description}"

class Order(TimeStampMixin):
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
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered')])

    def __str__(self):
        return f"Order #{self.id} by {self.customer.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the order first

        self.calculate_total_amount()

        super().save(*args, **kwargs)
    
    def calculate_total_amount(self):
        total_amount = 0
        order_products = self.orderproduct_set.all()

        for order_product in order_products:
            purchase_order_product = PurchaseOrderProduct.objects.filter(
                product=order_product.product,
                quantity__gt=0
            ).first()

            if purchase_order_product:
                total_amount += purchase_order_product.price * order_product.quantity

        self.total_amount = total_amount
        self.pending_amount = total_amount - self.paid_amount

        self.record_general_ledger_entries()
    
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

        Payment.objects.create(order=self, amount_paid=amount_paid)

        self.pending_amount -= amount_paid
        if self.pending_amount <= 0:
            self.payment_status = 'PAID'
            self.pending_amount = 0
        else:
            self.payment_status = 'PARTIALLY PAID'
        
class Payment(TimeStampMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)

class OrderProduct(TimeStampMixin):
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

class OrderReturn(TimeStampMixin):
    ordered_product = models.ForeignKey(OrderProduct, on_delete=models.CASCADE, related_name='returns')
    return_date = models.DateTimeField(default=timezone.now)
    quantity_returned = models.PositiveIntegerField()

    def save(self, *args, **kwargs):

        if not self.pk:
            product = self.ordered_product.product
            product.stock_quantity += self.quantity_returned
            product.save()

        super().save(*args, **kwargs)

# Purchase Order Management

class PurchaseOrder(TimeStampMixin):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='PurchaseOrderProduct')
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Received', 'Received')])

    def __str__(self):
        return f"Purchase Order #{self.id} from {self.supplier.name}"

class PurchaseOrderProduct(TimeStampMixin):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in Purchase Order #{self.purchase_order.id}"

class InventoryBatch(TimeStampMixin):
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

class AccountTransaction(TimeStampMixin):
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
class InventoryTransaction(TimeStampMixin):
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
class Employee(TimeStampMixin):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Distribution Planning
class DeliveryRoute(TimeStampMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    route_details = models.TextField()
    estimated_delivery_time = models.DateTimeField()

    def __str__(self):
        return f"Route for Order #{self.order.id}"