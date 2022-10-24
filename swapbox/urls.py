from django.contrib import admin
from django.urls import path,include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('my_accounts/',include('accounts.urls')),
    path('shop/',include('shop.urls',namespace='shop')),
    path(r'',views.index_view),
    path(r'dashboard/',include('profiles.urls')),
    path(r'payments/',include('payments.urls')),
]

#appending the static files urls to the above media
urlpatterns += staticfiles_urlpatterns()
#how to upload media..appending the media url to the patterns above
