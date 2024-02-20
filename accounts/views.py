from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required()
def account_details_view(request,id):
    pass

@login_required()
def account_impressions(request,id):
    pass

@login_required()
def edit_account_details_view(request,id):
    pass

@login_required()
def update_account_market_price(request,id):
    pass