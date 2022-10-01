from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path(r'',views.dashboard,name='dashboard'),
    path(r'change_mode/',views.change_user_mode,name='change_mode'),
]
