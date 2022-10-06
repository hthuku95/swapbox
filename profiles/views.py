from django.shortcuts import render,redirect
from .models import UserProfile
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required()
def dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)

    context = {
        'user_profile':user_profile
    }

    return render(request, "profiles/dashboard.html",context)


# For now, the process for changing the user mode will be hidden inside the dashbord
# When we merge react frontend, it will be a button accesible on the drop-down Menu
@login_required()
def change_user_mode(request):
    user_profile = UserProfile.objects.get(user=request.user)

    if user_profile.mode == 'S':
        user_profile.mode = 'B'
        user_profile.save()
        messages.success(request, "You have successfully switched to Buyer Mode")
        return redirect('profiles:dashboard')
    else:
        user_profile.mode = 'S'
        user_profile.save()
        messages.success(request, "You have successfully switched to Seller Mode")
        return redirect('profiles:dashboard')
