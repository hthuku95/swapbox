from django.contrib import admin
from django.urls import path,include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path(r'admin/', admin.site.urls),
    path(r'accounts/', include('allauth.urls')),
    path(r'my_accounts/', include('accounts.urls')),
    path(r'shop/', include('shop.urls', namespace='shop')),
    path(r'bitcoin/', include('voltage_payments.urls')),
    path(r'dashboard/', include('profiles.urls')),
    path(r'payments/', include('payments.urls')),
    path(r'healthz', views.health_check, name='health-check'),
    path(r'', views.index_view),
]

#appending the static files urls to the above media
urlpatterns += staticfiles_urlpatterns()
#how to upload media..appending the media url to the patterns above
