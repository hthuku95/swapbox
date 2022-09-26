from django.db import models
from profiles.models import UserProfile
from django.db.models.signals import post_save
from accounts.models import Account
# Create your models here.

class Cart(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    accounts = models.ManyToManyField(Account, blank=True)

    def __str__(self):
        return self.user.user.username

    def get_total(self):
        pass

class Wishlist(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    accounts = models.ManyToManyField(Account, blank=True)

    def __str__(self):
        return self.user.user.username
    
    def get_total(self):
        pass

# Creating a wishlist and a cart when a new user is created
def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        cart = Cart.objects.create(user=instance)
        wishlist = Wishlist.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=UserProfile)