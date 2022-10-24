from django.shortcuts import render
from .models import Payment, Order, BillingAddress
# Create your views here.

def payment_details(request,id):
    
    return render(request, "payments/payment_details.html")