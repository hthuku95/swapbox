from django.db import models
from shop.models import Cart
from profiles.models import UserProfile


# Create your models here.
ORDER_TYPE_CHOICES = (
    ('AU','Account Upload'),
    ('AP','Account Purchase'),
    ('PC','Price Change')
)

PAYMENT_METHOD_CHOICES = (
    ('PC','Paypal or Card'),
    ('W','Wallet')
)

class BillingAddress(models.Model):
    user = models.ForeignKey(UserProfile, blank=True,null=True, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100,blank=True,null=True)
    apartment_address = models.CharField(max_length=100,blank=True,null=True)
    zip = models.CharField(max_length=100)
    default = models.BooleanField(default=False)

    def __str__(self):
        return "Address "+self.street_address +" - "+self.zip
    
class Order(models.Model):
    reference_code = models.CharField( max_length=50)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL,blank=True,null=True)
    value = models.FloatField(default=0.0)
    billing_address = models.ForeignKey(BillingAddress, blank=True,null=True, on_delete=models.SET_NULL)
    payment_method = models.CharField(choices=PAYMENT_METHOD_CHOICES,blank=True,null=True, max_length=2)
    payment_complete = models.BooleanField(default=False)
    order_type = models.CharField(choices=ORDER_TYPE_CHOICES, max_length=2,blank=True,null=True)

    def __str__(self):
        return "ORDER "+ self.reference_code

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return "Payment for Order -"+self.order.reference_code
    


    
