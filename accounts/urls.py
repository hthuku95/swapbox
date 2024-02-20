from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path(r'account_details/<int:id>/',views.account_details_view,name='account-detail-view'),
    path(r'account_impressions/<int:id>/',views.account_impressions,name='account-impressions'),
    path(r'edit_account_details/<int:id>/',views.edit_account_details_view,name='edit-account-details'),
    path(r'update_account_market_price/<int:id>/',views.update_account_market_price,name='update-account-market-price'),
]