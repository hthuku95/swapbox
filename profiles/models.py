from django.db import models
from django.conf import settings
from django.db.models.signals import post_save

# Create your models here.
MODE_CHOICES = (
    ('S','Seller'),
    ('B','Buyer'),
)
class ProfileSettings(models.Model):
    pass
class Wallet(models.Model):
    pass

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mode = models.CharField(choices=MODE_CHOICES, max_length=2,blank=True,null=True)
    profile_settings = models.ForeignKey(ProfileSettings, blank=True,null=True, on_delete=models.SET_NULL)
    wallet = models.ForeignKey(Wallet, blank=True,null=True, on_delete=models.SET_NULL)

    # Credit/Debit Cards
    # Paypal Accounts

    # How can you securely save Credit/Debit card information?

    def __str__(self):
        return self.user.username


def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance,mode='B')


post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)
