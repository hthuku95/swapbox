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
    has_test = models.BooleanField(default=False)

    # User can only add three images
    images = models.ManyToManyField(Image,blank=True)

    # User can only add 5 tags
    tags = models.ManyToManyField(Tag,blank=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=2)

    chat = models.ForeignKey(Chat, blank=True,null=True, on_delete=models.CASCADE)

    ratings = models.FloatField(blank=True,null=True)
    reviews  = models.FloatField(blank=True,null=True)
    number_of_completed_orders = models.FloatField(blank=True,null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("shop:account-detail-view", kwargs={
        'id': self.id
    })

    def get_final_price(self):
        if self.discount_price:
            return discount_price
        else:
            return self.selling_price
        
    def get_market_fee(self):
        return self.market_fee
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

    
