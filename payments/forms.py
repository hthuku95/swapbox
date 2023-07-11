from django import forms

class CheckoutForm(forms.Form):
    PAYMENT_METHOD_CHOICES = (
        ('PC','Paypal or Card'),
        ('W','Wallet')
    )
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_zip = forms.CharField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)
    
    payment_method = forms.ChoiceField(widget=forms.RadioSelect, choices=PAYMENT_METHOD_CHOICES)
