from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Payment, Order, BillingAddress
from shop.models import Cart
from .forms import CheckoutForm
from profiles.models import UserProfile
from django.contrib import messages
import random
import string
import logging
import datetime

logger = logging.getLogger(__name__)

# Create your views here.
def generate_reference_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

@login_required()
def payment_details(request,slug):
    order = Order.objects.get(reference_code = slug)
    userprofile = UserProfile.objects.get(user=request.user)
    timestamp  = datetime.datetime.now()

    logger.info(f"{timestamp} fetching payment details of User {userprofile.user.username}")

    context = {
        'order':order,
        'userprofile':userprofile
    }
    
    return render(request, "payments/payment_details.html",context)

@login_required()
def checkout_view(request):
    # Remember to handle all tthe three order type scenarios
    userprofile = UserProfile.objects.get(user=request.user)
    cart = Cart.objects.get(user=userprofile)

    context = {
        'cart':cart,
        'userprofile':userprofile
    }
    # Fetching Default Billing Address
    try:
        billing_address_qs = BillingAddress.objects.filter(
            user=userprofile,
            default=True
        )

        if billing_address_qs.exists():
            context.update(
                {'default_billing_address': billing_address_qs[0]})
        timestamp = datetime.datetime.now()
    except Exception as e:
        logger.exception(f"{timestamp}: Exception: {e}")
        logger.error(f"{timestamp}: Error fetching Default billing Address of user:{userprofile.user.username}")

    if request.method == 'POST':
        # Fetching Form
        try:
            logger.info(f"{timestamp} Checking validity of data from checkout form of user{userprofile.user.username}")
            form =CheckoutForm(request.POST)
        except:
            logger.exception(f"{timestamp}: Exception: {e}")
            logger.error(f"{timestamp}: Error Fetchin Checkout Form: {form}  from User {userprofile}")
        if form.is_valid():
            try:
                # fetching order
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
                        value = cart.get_total_price_of_accounts_to_be_purchased(),
                        order_type = 'AP'
                    )
                    order.save()
            except Exception as e:
                logger.exception(f"{timestamp}: Exception: {e}")
                logger.error(f"{timestamp}: Error Fetching/creating order {order} of User {userprofile}")
            
            payment_method = form.cleaned_data['payment_method']
            
            # Handle Bitcoin payment
            if payment_method == 'BTC':
                order.payment_method = payment_method
                order.save()
                messages.info(request, "Redirecting to Bitcoin payment...")
                return redirect('voltage_payments:create_payment', order_id=order.id)

            # Using Default Biing Address
            try:
                use_default_billing = form.cleaned_data.get(
                        'use_default_billing'
                    )
            except Exception as e:
                logger.exception(f"{timestamp}: Exception: {e}")
                logger.error(f"{timestamp}: Error Fetching the 'Use Default Billing Address' from Checkout form from user {userprofile}")


            if use_default_billing:
                try:
                    logger.info(f"{timestamp}: Using the defualt billing address for User{userprofile}")
                    address_qs = BillingAddress.objects.filter(
                        user=userprofile,
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.payment_method = payment_method
                        order.save()

                        messages.success(request,"Using default billing address")
                        return redirect('/payments/payment/'+order.reference_code+'/')
                except Exception as e:
                    logger.exception(f"{timestamp}: Exception: {e}")
                    logger.error(f"{timestamp}: Error Fetchin Default Billing Address of User {userprofile}")

                else:
                    messages.warning(request,"You dont have a default billing address")
                    return redirect("payments:checkout-view")
            else:
                # User is entering a new billing Address
                try:
                    logger.info(f"{timestamp}: User {userprofile} is entering a new billing Address")
                    m_billing_address = form.cleaned_data['billing_address']
                    m_billing_address2 = form.cleaned_data['billing_address2']
                    m_billing_zip = form.cleaned_data['billing_zip']
                    m_first_name = form.cleaned_data['first_name']
                    m_last_name = form.cleaned_data['last_name']
                    try:
                        user = request.user
                        logger.info(f"{timestamp}: proceesing New Billing Address info of User {userprofile.user.username}")
                        if user.first_name and user.last_name:
                            address = BillingAddress(
                                        user = userprofile,
                                        street_address=m_billing_address,
                                        apartment_address=m_billing_address2,
                                        zip=m_billing_zip)
                            address.save()

                            # Setting default billing address
                            set_default_billing = form.cleaned_data.get(
                                    'set_default_billing'
                                )

                            if set_default_billing:
                                address.default = True
                                address.save()

                            order.billing_address = address
                            order.payment_method = payment_method
                            order.save()
                            logger.info(f"{timestamp}: New Billing Address of User {userprofile.user.username} Saved Successfully")
                        else:
                            logger.info(f"{timestamp}: Adding the First and Last Name of User {userprofile.user.username}")
                            logger.info(f"{timestamp}: First Name: {user.first_name} || Last Name: {user.last_name}")
                            user.first_name = m_first_name
                            user.save()
                            user.last_name = m_last_name
                            user.save()

                            address = BillingAddress(
                                        user = userprofile,
                                        street_address=m_billing_address,
                                        apartment_address=m_billing_address2,
                                        zip=m_billing_zip)
                            address.save()
                            logger.info(f"{timestamp}: New Billing Address of User {userprofile.user.username} Saved Successfully")

                            # Setting default billing address
                            logger.info(f"Setting Default Billing Address")
                            set_default_billing = form.cleaned_data.get(
                                    'set_default_billing')

                            if set_default_billing:
                                address.default = True
                                address.save()
                            
                            order.billing_address = address
                            order.payment_method = payment_method
                            order.save()

                        messages.success(request,"Billing address saved succesfully. Complete payment!")
                        return redirect('/payments/payment/'+order.reference_code+'/')

                    except Exception as e:
                        messages.warning(request,"Please enter all the required fields")
                        print(e)
                        return redirect("payments:checkout-view")
                except Exception as e:
                    logger.exception(f"{timestamp}: Exception {e}")
                    logger.error(f"{timestamp}: Error setting New Billing Address for user {userprofile}")
        else:
            messages.warning(request,"Plese complete all the required fields")
            print("exception occured or something")
            return redirect("payments:checkout-view")
    else:
        form = CheckoutForm()
        context.update({
            'form':form
        })
    return render(request, "payments/checkout.html",context)