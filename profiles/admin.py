from django.contrib import admin
from .models import UserProfile,Wallet,ProfileSettings,CreditCard,PayPalAccount
# Register your models here.

admin.site.register(UserProfile)
admin.site.register(Wallet)
admin.site.register(ProfileSettings)
admin.site.register(CreditCard)
admin.site.register(PaypalAccount)