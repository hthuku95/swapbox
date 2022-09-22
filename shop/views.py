from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user
from accounts.models import Tag,Image,Account

# Create your views here.

# article list page
def market(request):
    accounts = Account.objects.all()
    tags = Tag.objects.all()
    images = Image.objects.all()

    context = {
        'accounts':accounts,
        'tags':tags,
        'images':images
    }
    return render(request,'shop/market.html',context)

# Account detail view
# From market perspective
def account_detail_view(request,id):
    account = Account.objects.get(id=id)
    
    context = {
        'account':account
    }

    return render(request,'shop/account_details.html',context)

# Add to cart
def add_to_cart(request,id):
    # if an account has an exam, redirect to the exam page, else add the account to the user's cart
    # Handle this with a pop-up
    pass

def remove_from_cart(request,id):
    pass

def add_to_wishlist(request,id):
    pass
