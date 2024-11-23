from django import forms
from django.forms import modelformset_factory
from .models import Order, OrderProduct

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer', 'booking_man', 'area', 'delivery_man', 
            'city', 'total_amount', 'paid_amount', 'payment_status', 'status'
        ]

class OrderProductForm(forms.ModelForm):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if product and quantity:
            if product.stock_quantity < quantity:
                if not product.on_backorder:
                    raise forms.ValidationError(
                        f"Quantity '{quantity}' exceeds available stock '{product.stock_quantity}' for product '{product.name}'."
                    )
        return cleaned_data

# Formset for OrderProduct
OrderProductFormSet = modelformset_factory(
    OrderProduct,
    form=OrderProductForm,
    extra=1,  # Allows adding one blank form by default
    can_delete=True,  # Enables deleting existing OrderProduct instances
)
