from django.contrib import admin
from .models import BillingAddress, Order, Payment
# Register your models here.

admin.site.register(BillingAddress)
admin.site.register(Order)
admin.site.register(Payment)