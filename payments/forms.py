from django import forms

class CheckoutForm(forms.Form):
    PAYMENT_METHOD_CHOICES = (
        ('PC','Paypal or Card'),        
        ('W','Wallet'),
        ('BTC','Bitcoin')
    )
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_zip = forms.CharField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)
    
    payment_method = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'}), choices=PAYMENT_METHOD_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to form fields
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['billing_address'].widget.attrs.update({'class': 'form-control'})
        self.fields['billing_address2'].widget.attrs.update({'class': 'form-control'})
        self.fields['billing_zip'].widget.attrs.update({'class': 'form-control'})

    def clean_payment_method(self):
        payment_method = self.cleaned_data.get('payment_method')
        if not payment_method:
            raise forms.ValidationError("Please select a payment method.")
        return payment_method
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        use_default_billing = cleaned_data.get('use_default_billing')
        
        # For Bitcoin payments, billing address is optional
        if payment_method == 'BTC':
            return cleaned_data
        
        # For other payment methods, validate billing info
        if not use_default_billing:
            required_fields = ['first_name', 'last_name', 'billing_address', 'billing_zip']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f'This field is required for {self.fields["payment_method"].choices[int(payment_method)-1][1]} payments.')
        
        return cleaned_data
