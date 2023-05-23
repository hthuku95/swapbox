from django import forms

PAYMENT_METHOD_CHOICES = [

]

class CheckoutForm(forms.Form):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_zip = forms.CharField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

# Add radio button for selecting payment method
class PaymentMethodForm(forms.Form):
    payment_method = forms.ComboField()