from django.contrib import admin
from .models import Account,Image,Impression,Tag,View,Credential
# Register your models here.


admin.site.register(Account)
admin.site.register(Image)
admin.site.register(Tag)
admin.site.register(Impression)
admin.site.register(View)
admin.site.register(Credential)