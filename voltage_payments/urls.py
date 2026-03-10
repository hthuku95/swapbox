from django.urls import path
from . import views

app_name = 'voltage_payments'

urlpatterns = [
    path('pay/<int:order_id>/',         views.create_payment,      name='create_payment'),
    path('info/<uuid:payment_id>/',     views.payment_info,        name='payment_info'),
    path('webhook/',                    views.voltage_webhook,     name='webhook'),
    path('status/<uuid:payment_id>/',   views.payment_status_api,  name='status_api'),
    path('history/',                    views.payment_list,        name='payment_list'),
]
