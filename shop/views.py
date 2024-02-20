from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user
from accounts.models import Tag,Image,Account
from profiles.models import UserProfile
from django.contrib import messages
from .models import Cart,Wishlist

# Create your views here.

# Market View
def market(request):
    accounts = Account.objects.filter(status='OS')

    context = {
        'accounts':accounts
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
@login_required()
def add_to_cart(request,id):
    account = get_object_or_404(Account, id=id)
    userprofile = UserProfile.objects.get(user=request.user)
    cart = Cart.objects.get(user=userprofile)
    
    if cart.accounts_to_be_purchased.filter(id=account.id).exists():
        messages.info(request,"The account is already in your Cart")
        return redirect("shop:market")
    elif account.status == 'IC':
        messages.warning(request,"The account has already been auctioned off. Browse our market page for other similar accounts")
        return redirect("shop:market")
    else:
        account.status = 'IC'
        account.save()

        # Remove the acount from other wishlists
        wish_lists = Wishlist.objects.filter(accounts__id=id)
        for wish_list in wish_lists:
            wish_list.accounts.remove(account)
            wish_list.save()

        cart.accounts_to_be_purchased.add(account)
        messages.success(request, "The account was added to your cart successfully")
        return redirect("shop:market")

@login_required()
def remove_from_cart(request,id):
    account = get_object_or_404(Account, id=id)
    userprofile = UserProfile.objects.get(user=request.user)
    cart = Cart.objects.get(user=userprofile)

    if cart.accounts_to_be_purchased.filter(id=account.id).exists():
        cart.accounts_to_be_purchased.remove(account)
        cart.save()
        account.status = 'OS'
        account.save()
        messages.success(request, "The account has been successfully removed from your cart")
        return redirect("shop:market")
    else:
        messages.info(request, "The account has already been removed from your Cart")
        return redirect("shop:market")

@login_required()
def add_to_wishlist(request,id):
    account = get_object_or_404(Account, id=id)
    userprofile = UserProfile.objects.get(user=request.user)
    wish_list = Wishlist.objects.get(user=userprofile)

    if wish_list.accounts.filter(id=account.id).exists():
        messages.info(request, "The account is already in your wishlist")
        return redirect("shop:market")
    elif account.status == 'IC':
        messages.warning(request,"The account has already been auctioned off.Browse our marketplace for other similar accounts")
        return redirect("shop:market")
    else:
        wish_list.accounts.add(account)
        messages.success(request, "The account has been added to your wishlist successfully")
        return redirect("shop:market")

@login_required()
def remove_from_wishlist(request,id):
    account = get_object_or_404(Account, id=id)
    userprofile = UserProfile.objects.get(user=request.user)
    wish_list = Wishlist.objects.get(user=userprofile)

    if wish_list.accounts.filter(id=account.id).exists():
        wish_list.accounts.remove(account)
        wish_list.save()
        messages.success(request, "The account was successfully removed from your Wishlist ")
        return redirect("shop:market")
    else:
        messages.info(request, "The account has already been removed from your wishlist")
        return redirect("shop:market")

@login_required()
def cart_view(request):
    userprofile = UserProfile.objects.get(user=request.user)
    cart = Cart.objects.get(user=userprofile)

    context = {
        'userprofile':userprofile,
        'cart':cart
    }

    return render(request, "shop/cart.html",context)

@login_required()
def wishlist_view(request):
    userprofile = UserProfile.objects.get(user=request.user)
    wishlist = Wishlist.objects.get(user=userprofile)

    context = {
        'userprofile':userprofile,
        'wishlist':wishlist
    }

    return render(request,"shop/wishlist.html",context)
