from django.db import models

# Inventory Management
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    lot_number = models.CharField(max_length=50)
    expiration_date = models.DateField()
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class InventoryBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=50)
    expiration_date = models.DateField()
    quantity = models.IntegerField()

    def __str__(self):
        return f"Batch {self.batch_number} of {self.product.name}"

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
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
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
    products = models.ManyToManyField(Product, through='OrderProduct')
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered')])

    def __str__(self):
        return f"Order #{self.id} by {self.customer.name}"

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in Order #{self.order.id}"

# Purchase Order Management
class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_info = models.TextField()

    def __str__(self):
        return self.name

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

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in Purchase Order #{self.purchase_order.id}"

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