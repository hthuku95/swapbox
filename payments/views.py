from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Payment, Order, BillingAddress
from shop.models import Cart
from .forms import CheckoutForm
from profiles.models import UserProfile
from django.contrib import messages
import random
import string

# Create your views here.
def generate_reference_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

@login_required()
def payment_details(request,slug):
    order = Order.objects.get(reference_code = slug)

    context = {
        'order':order
    }
    
    return render(request, "payments/payment_details.html")

@login_required()
def checkout_view(request):
    # Remember to handle all tthe three order type scenarios
    userprofile = UserProfile.objects.get(user=request.user)
    cart = Cart.objects.get(user=userprofile)

    context = {
        'cart':cart
    }

    billing_address_qs = BillingAddress.objects.filter(
        user=userprofile,
        default=True
    )

    if billing_address_qs.exists():
        context.update(
            {'default_billing_address': billing_address_qs[0]})

    if request.method == 'POST':
        form =CheckoutForm(request.POST)

        if form.is_valid():
            order_qs = Order.objects.filter(
                cart = cart,
                order_type = 'AP',
                payment_complete = False
            )
            if order_qs.exists():
                order = order_qs[0]
            else:
                order = Order(
                    reference_code = generate_reference_code(),
                    cart = cart,
                    value = cart.get_total_price_of_accounts_to_be_purchased()
                    order_type = 'AP'
                )
                order.save()
            use_default_billing = form.cleaned_data.get(
                    'use_default_billing')

            if use_default_billing:
                print("Using the defualt billing address")
                address_qs = BillingAddress.objects.filter(
                    user=userprofile,
                    default=True
                )
                if address_qs.exists():
                    billing_address = address_qs[0]
                    order.billing_address = billing_address
                    order.save()

                    messages.success(request,"Using default billing address")
                    # how to add slug field to this
                    return redirect('/payments/payment/'+order.reference_code+'/')
                else:
                    messages.warning(request,"You dont have a default billing address")
                    return redirect("payments:checkuot-view")

            else:
                # User is entering a new billing Address
                m_billing_address = form.cleaned_data['billing_address']
                m_billing_address2 = form.cleaned_data['billing_address2']
                m_billing_zip = form.cleaned_data['billing_zip']
                m_first_name = form.cleaned_data['first_name']
                m_last_name = form.cleaned_data['last_name']
                m_payment_method = form.cleaned_data['payment_method']
                try:
                    user = request.user

                    if user.first_name and user.last_name:
                        address = Address(
                                    user = request.user,
                                    street_address=m_billing_address,
                                    apartment_address=m_billing_address2,
                                    first_name=m_first_name,
                                    last_name=m_last_name,
                                    zip=m_billing_zip)
                        address.save()
                    else:
                        user.first_name = m_first_name
                        user.save()
                        user.last_name = m_last_name
                        user.save()

                        address = Address(
                                    user = request.user,
                                    street_address=m_billing_address,
                                    apartment_address=m_billing_address2,
                                    first_name=m_first_name,
                                    last_name=m_last_name,
                                    zip=m_billing_zip)
                        address.save()

                    # Setting default billing address
                    set_default_billing = form.cleaned_data.get(
                            'set_default_billing')

                    if set_default_billing:
                        address.default = True
                        address.save()
                        
                    order.billing_address = address
                    order.payment_method = m_payment_method
                    order.save()

                    messages.success(request,"Billing address saved succesfully. Complete payment!")
                    return redirect('/payments/payment/'+order.reference_code+'/')

                except Exception as e:
                    messages.warning(request,"Please enter all the required fields")
                    print(e)
                    return redirect("payments:checkuot-view")
        else:
            messages.warning(request,"Plese complete all the required fields")
            print("exception occured or something")
            return redirect("payments:checkuot-view")
    else:
        form = CheckoutForm()
        context.update({
            'form':form
        })

    return render(request, "payments/checkout.html",context)