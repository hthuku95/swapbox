from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path(r'',views.market, name='market'),
    path(r'account/<int:id>/',views.account_detail_view,name='account-detail-view'),
    path(r'account/add_to_cart/<int:id>/',views.add_to_cart,name='add-to-cart-url'),
    path(r'account/remove_from_cart/<int:id>/',views.remove_from_cart,name='remove-from-cart-url'),
    path(r'account/add_to_wishlist/<int:id>/',views.add_to_wishlist,name='add-to-wishlist-url'),
    path(r'account/remove_from_wishlist/<int:id>/',views.remove_from_wishlist,name='remove-from-wishlist-url'),
]