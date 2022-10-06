from django.contrib import admin
from .models import BillingAddress, Order
# Register your models here.

admin.site.register(BillingAddress)
admin.site.register(Order)