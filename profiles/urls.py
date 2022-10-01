from django.urls import path
from . import views


urlpatterns = [
    path(r'',views.dashboard,name='dashboard'),
]
