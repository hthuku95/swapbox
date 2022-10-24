from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path(r'payment/<int:id>/',views.payment_details,name='payment-details'),
]