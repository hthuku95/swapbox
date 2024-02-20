from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path(r'payment/<slug>/',views.payment_details,name='payment-details'),
    path(r'checkout/',views.checkout_view,name='checkout-view'),
]