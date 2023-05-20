from django.db import models
from profiles.models import UserProfile
from chat.models import Chat
from django.shortcuts import reverse
# Create your models here.

STATUS_CHOICES = (
    ('S', 'Sold'),
    ('D', 'Draft'),
    ('OS', 'Onsale'),
    ('IC', 'InsideCart')
    # When an account is IC it will still be displayed on the Onsale panel of the seller
)

class Image(models.Model):
    image = models.FileField(max_length=100)

    def __str__(self):
        return self.id

# the user does not have to create a new tag everytime 
class Tag(models.Model):
    name = models.CharField(blank=True, null=True, max_length=50)
    
    def __str__(self):
        return self.name
    

class Account(models.Model):
    current_owner = models.ForeignKey(UserProfile,null=True,blank=True, on_delete=models.SET_NULL)
    uploaded_by = models.ForeignKey(UserProfile,null=True,blank=True,related_name='first_owner', on_delete=models.SET_NULL)
    date_uploaded = models.DateTimeField(auto_now_add=True)
    date_uploaded_on_market = models.DateTimeField(auto_now_add=False,blank=True,null=True)
    # When an account is added to a cart it is removed from the market
    # If the account stays in a cart for 24hrs without being purchased it will be re-uploaded to the market
    # How to set an arlam in python, or a timer
    date_removed_from_market = models.DateTimeField(auto_now_add=False,blank=True,null=True)
    platform = models.CharField(blank=True,null=True, max_length=50)
    url = models.URLField(blank=True,null=True, max_length=200)
    title = models.CharField(blank=True,null=True, max_length=50)
    thumb_nail = models.FileField(blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    selling_price = models.FloatField(blank=True,null=True)
    discount_price = models.FloatField(blank=True,null=True)

    market_fee = models.FloatField(blank=True,null=True)
    market_fee_after_price_change = models.FloatField(blank=True,null=True)

    reference_id = models.CharField(blank=True,null=True, max_length=50)
    verified_and_securely_transfared = models.BooleanField(default=False)
    no_of_times_price_has_changed = models.IntegerField(default = 0)

    # User can only add three images
    images = models.ManyToManyField(Image,blank=True)

    percent_of_complete_details = models.FloatField(default=0.0)
    # User can only add 5 tags
    tags = models.ManyToManyField(Tag,blank=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=2)

    chat = models.ForeignKey(Chat, blank=True,null=True, on_delete=models.CASCADE)

    ratings = models.FloatField(blank=True,null=True)
    reviews  = models.FloatField(blank=True,null=True)
    number_of_completed_orders = models.FloatField(blank=True,null=True)
    market_fee_payment_completed = models.BooleanField(default=False)
    last_time_account_was_edited = models.DateTimeField(blank=True,null=True, auto_now=False, auto_now_add=False)

    def __str__(self):
        return "Account - "+self.title

    def get_absolute_url(self):
        return reverse("accounts:account-detail-view", kwargs={
            'id': self.id
        })

    def get_impressions_url(self):
        return reverse("accounts:account-impressions", kwargs={
            'id':self.id
        })

    def get_edit_account_details_url(self):
        return reverse("accounts:edit-account-details", kwargs={
            'id':self.id
        })
    
    def get_update_market_price_url(self):
        return reverse("accounts:update-account-market-price",kwargs={
            'id':self.id
        })
        
    def get_absolute_market_url(self):
        return reverse("shop:account-market-detail-view", kwargs={
        'id': self.id
    })

    def get_final_price(self):
        if self.discount_price:
            return discount_price
        else:
            return self.selling_price
        
    def get_market_fee(self):
        return self.market_fee

    def get_market_fee_after_price_change(self):
        return self.market_fee_after_price_change
        
    # When one user adds an account to cart, the account is temporarily removed from the marketplace
    def get_add_to_cart_url(self):
        return reverse("shop:add-to-cart-url", kwargs={
            'id':self.id
        })
    
    def get_remove_from_cart_url(self):
        return reverse("shop:remove-from-cart-url", kwargs={
            'id':self.id
        })

    def get_add_to_wishlist_url(self):
        return reverse("shop:add-to-wishlist-url",kwargs={
            'id':self.id
        })

    def get_remove_from_wishlist_url(self):
        return reverse("shop:remove-from-wishlist-url",kwargs={
            'id':self.id
        })

class Credential(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    login_email = models.CharField(blank=True,null=True, max_length=512)
    login_username = models.CharField(blank=True,null=True, max_length=512)
    login_email_password = models.CharField(blank=True,null=True, max_length=512)
    recovery_email = models.CharField(blank=True,null=True, max_length=512)
    recovery_email_password = models.CharField(blank=True,null=True, max_length=512)
    # For Google allauth accounts
    login_gmail = models.CharField(blank=True,null=True, max_length=512)
    login_gmail_password = models.CharField(blank=True,null=True, max_length=512)
    recovery_gmail = models.CharField(blank=True,null=True, max_length=512)
    recovery_gmail_password = models.CharField(blank=True,null=True, max_length=50)
    allowed_viewers = models.ManyToManyField(UserProfile, blank=True)

    def __str__(self):
        return 'CREDENTIALS FOR ACCOUNT' + self.account.title
    
    
    

class View(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id
    

class Impression(models.Model):
    account = models.OneToOneField(Account, blank=True,null=True, on_delete=models.CASCADE)
    no_of_searches = models.IntegerField(default=0)
    internal_views = models.ManyToManyField(View, blank=True,related_name="Internal views+")
    views = models.ManyToManyField(View,blank=True,related_name="View+")
    no_of_wishlist = models.IntegerField(default=0)
    no_of_pending_carts = models.IntegerField(default=0)

    def __str__(self):
        return "ACCOUNT - "+ self.account.title
    
    def get_number_of_views(self):
        pass

    def get_number_of_internal_views(self):
        pass
