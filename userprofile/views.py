from django.shortcuts import render , redirect,get_object_or_404
from authentication1.models import usertable
from adminapp.models import WalletTransaction,Wallet
from django.db import transaction
from django.contrib import messages
from .models import UserAddress
from django.contrib.auth.hashers import check_password
import re
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.utils import timezone 
from datetime import datetime
import os
from django.shortcuts import get_object_or_404
import json
from django.contrib.auth import update_session_auth_hash
from user.models import Order,OrderItem
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import tempfile
import asyncio
from pyppeteer import launch  
import os
import tempfile

import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from django.contrib.auth.decorators import login_required   
from decimal import Decimal

# Create your views here.
import razorpay
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))



@login_required(login_url='login')
def userprofile(request):
    user = request.user
    print(user.refferal_code)
    if request.method == 'POST':
        
        firstname = request.POST.get('firstname', '').strip()
        lastname = request.POST.get('lastname', '').strip()
        phonenumber = request.POST.get('phonenumber', '').strip()
        print(f"Debug - User referral code: {user.refferal_code}")
       
        has_error = False
        
       
        if not firstname:
            messages.error(request, 'First name cannot be empty.')
            has_error = True
        elif len(firstname) > 50:
            messages.error(request, 'First name is too long (maximum 50 characters).')
            has_error = True
        
        
        if not lastname:
            messages.error(request, 'Last name cannot be empty.')
            has_error = True
        elif len(lastname) > 50:
            messages.error(request, 'Last name is too long (maximum 50 characters).')
            has_error = True
        
       
        if not phonenumber:
            messages.error(request, 'Phone number cannot be empty.')
            has_error = True
        elif not phonenumber.isdigit():
            messages.error(request, 'Phone number should contain only digits.')
            has_error = True
        elif len(phonenumber) < 10 or len(phonenumber) > 15:
            messages.error(request, 'Phone number should be between 10 and 15 digits.')
            has_error = True
            
      
        if not has_error:
            user.firstname = firstname
            user.lastname = lastname
            user.phonenumber = phonenumber
            user.save()
            messages.success(request, 'Profile updated successfully!')
        
        return redirect('userprofile')
    
    context = {
        'user': user,
        'referral_code': user.refferal_code
    }
    return render(request, 'userprofile.html', context)

# ##################################################################my account#######################################################################
@login_required
def myaccount(request):
   
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'balance': 0.00}
    )
    
    
    recent_transactions = WalletTransaction.objects.filter(
        wallet=wallet
    ).order_by('-transaction_time')[:5]  
    
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'myaccount.html', context)

@login_required
def wallet_transactions(request):
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'balance': 0.00}
    )
    
    all_transactions = WalletTransaction.objects.filter(
        wallet=wallet
    ).order_by('-transaction_time')
    
    transaction_type = request.GET.get('type', '')
    search_query = request.GET.get('search', '')

    if transaction_type:
        if transaction_type == 'add':
            all_transactions = all_transactions.filter(transaction_type='add')
        elif transaction_type == 'deduct':
            all_transactions = all_transactions.filter(transaction_type='deduct')
        elif transaction_type == 'refund':
            all_transactions = all_transactions.filter(transaction_type='refund')
    
    if search_query:
        all_transactions = all_transactions.filter(description__icontains=search_query)

    paginator = Paginator(all_transactions, 10) 
    page_number = request.GET.get('page', 1)
    transactions = paginator.get_page(page_number)


    context = {
        'wallet': wallet,
        'transactions': transactions,
        'current_type': transaction_type,
        'search_query': search_query,
    }
    
    return render(request, 'wallet_transactions.html', context)



@login_required
def address(request):
    user = request.user
    addresses = UserAddress.objects.filter(user=user)
    
    context = {
        'addresses': addresses
    }
    return render(request, 'address.html', context)

from django.http import JsonResponse
from django.views.decorators.http import require_POST


@require_POST
def set_default_address(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        address_id = data.get('address_id')
        
        address = UserAddress.objects.get(address_id=address_id, user=request.user)
        
        # Reset all addresses to non-default first
        UserAddress.objects.filter(user=request.user).update(is_default=False)
        
        # Set this one as default
        address.is_default = True
        address.save()
        
        return JsonResponse({'success': True})
    except UserAddress.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Address not found'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

@login_required
def delete_address(request, address_id):
    if request.method == 'POST':
        address = get_object_or_404(UserAddress, address_id=address_id, user=request.user)
        address.delete()
        messages.success(request, 'Address deleted successfully!')
    return redirect('address')

@login_required
def editaddress(request, address_id=None):
    if address_id:
        # Edit existing address
        address = get_object_or_404(UserAddress, address_id=address_id, user=request.user)
        
        if request.method == 'POST':
            address.full_name = request.POST.get('full_name')
            address.phone_number = request.POST.get('phone_number')
            address.country = request.POST.get('country')
            address.state = request.POST.get('state')
            address.city = request.POST.get('city')
            address.postal_code = request.POST.get('postal_code')
            address.address_line1 = request.POST.get('address_line1')
            address.address_line2 = request.POST.get('address_line2', '')
            address.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('address')
    else:
        # Add new address
        address = None
        if request.method == 'POST':
            new_address = UserAddress(
                user=request.user,
                full_name=request.POST.get('full_name'),
                phone_number=request.POST.get('phone_number'),
                country=request.POST.get('country'),
                state=request.POST.get('state'),
                city=request.POST.get('city'),
                postal_code=request.POST.get('postal_code'),
                address_line1=request.POST.get('address_line1'),
                address_line2=request.POST.get('address_line2', ''),
                is_default=not UserAddress.objects.filter(user=request.user).exists()  
            )
            new_address.save()
            messages.success(request, 'New address added successfully!')
            return redirect('address')
    
    context = {
        'address': address
    }
    return render(request, 'editaddress.html', context)


# ###########################################################my orders#######################################################################
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')

    for order in orders:
        # Calculate active items (not cancelled)
        order.active_items = order.items.filter(is_cancelled=False)
        
        # Format order ID for display
        order.formatted_id = f"PF-{order.order_date.strftime('%Y%m%d')}-{str(order.id).zfill(4)}"
        
        # Ensure grand total properties are properly calculated
        # (These are properties on the Order model, so they should already work)
       
    paginator = Paginator(orders, 2) 
    page = request.GET.get('page')
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders,
        'current_brand': None,
    }
    return render(request, 'myorders.html', context)

from django.urls import reverse
# Fixed retry_payment view
@login_required
def retry_payment(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
        
    try:
        # Add more logging to debug the issue
        logger.info(f"Retry payment requested for order: {order_id} by user: {request.user.id}")
        
        order = Order.objects.get(id=order_id, user=request.user)
        
        # Check if order needs payment retry - be more permissive in conditions
        if order.order_status == 'Completed' or order.payment_status == 'paid':
            return JsonResponse({'success': False, 'message': 'This order does not require payment retry'})
        
        try:
            # Initialize Razorpay client
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Create Razorpay order
            razorpay_order = client.order.create({
                'amount': int(float(order.total_amount) * 100),  # Ensure proper conversion
                'currency': 'INR',
                'receipt': f'order_{order.id}_retry',
                'payment_capture': '1'
            })
            
            logger.info(f"Razorpay order created: {razorpay_order['id']} for order: {order.id}")
            
            # Update order with new Razorpay ID
            order.razorpay_order_id = razorpay_order['id']
            order.save()
            
            # Get user info for payment
            phone = ''
            if hasattr(order, 'shipping_address') and order.shipping_address:
                phone = order.shipping_address.phone_number
            
            # Prepare payment data
            payment_data = {
                'key_id': settings.RAZORPAY_KEY_ID,
                'amount': int(float(order.total_amount) * 100),
                'currency': 'INR',
                'order_id': razorpay_order['id'],
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'phone': phone,
                'confirmation_url': reverse('order_confirmation', args=[order.id])
            }
            
            return JsonResponse({
                'success': True,
                'payment_data': payment_data,
                'message': 'Redirecting to payment gateway'
            })
            
        except Exception as e:
            logger.error(f"Razorpay error: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Payment gateway error: {str(e)}'}, status=500)
            
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)
    except Exception as e:
        logger.error(f"Error retrying payment: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'}, status=500)
    

def payment_success(request):
    payment_id = request.GET.get('payment_id')
    order_id = request.GET.get('order_id')
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        # Update order status
        order.payment_status = 'Completed'
        order.save()
        
        # Use a direct URL path instead of a named URL to avoid app namespace issues
        return redirect(f'/order-confirmation/{order.id}/')
        
    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)



from django.db.models import F
import traceback



@login_required
@transaction.atomic
def cancel_order(request, order_id):
    if request.method == 'POST':
        try:
            logger = logging.getLogger(__name__)
            data = json.loads(request.body)
            reason = data.get('reason', '')
            
            logger.info(f"Starting cancellation for order {order_id}, reason: {reason}")
            
            # Lock the order row to prevent concurrent modifications
            order = Order.objects.select_for_update().get(id=order_id, user=request.user)
            
            logger.info(f"Found order: ID={order_id}, status={order.order_status}, "
                       f"payment={order.payment_status}, amount={order.total_amount}")
            
            if order.is_cancelled:
                logger.info(f"Order {order_id} is already cancelled")
                return JsonResponse({
                    'success': False,
                    'message': 'This order has already been cancelled'
                })
            
            # Handle shipped orders (admin approval required)
            if order.order_status == 'Shipped':
                logger.info(f"Order {order_id} is shipped, submitting cancellation request")
                order.cancel_description = reason
                order.cancel_request_date = timezone.now()
                order.cancel_request_status = 'Requested'
                order.save()
                
                return JsonResponse({
                    'success': True,
                    'is_request': True,
                    'message': 'Cancellation request submitted successfully.'
                })
                
            # Handle cancellable orders (Pending/Processing)
            elif order.order_status in ['Pending', 'Processing']:
                logger.info(f"Processing immediate cancellation for order {order_id}")
                order_items = order.items.select_related('product_variation').all()
                logger.info(f"Found {order_items.count()} items to cancel")
                
                # Return stock and mark items as cancelled
                for item in order_items:
                    if item.product_variation:
                        logger.info(f"Returning {item.quantity} stock for product variation {item.product_variation.id}")
                        item.product_variation.stock += item.quantity
                        item.product_variation.save()
                    
                    item.is_cancelled = True
                    item.save()
                
                # Process refund if payment was completed
                if order.payment_status == 'PAID' and order.payment_method in ['Razorpay', 'Wallet']:
                    logger.info(f"Processing refund for paid order {order_id}, amount: {order.total_amount}")
                    
                    try:
                        # Get or create user wallet
                        wallet, created = Wallet.objects.get_or_create(user=request.user)
                        
                        # Add refund amount to wallet
                        previous_balance = wallet.balance
                        wallet.balance += order.total_amount
                        wallet.save()
                        
                        # Create wallet transaction record
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_type='refund',
                            transaction_amount=order.total_amount,
                            description=f"Refund for cancelled order #{order_id}",
                        )
                        
                        # Update order refund details
                        order.refund_amount = order.total_amount
                        order.refund_date = timezone.now()
                        order.payment_status = 'Refunded'
                        
                        logger.info(f"Refund processed successfully. Wallet balance updated from {previous_balance} to {wallet.balance}")
                        
                    except Exception as wallet_error:
                        logger.error(f"failed to process refund: {str(wallet_error)}")
                        # Continue with cancellation even if refund fails
                
                # Update order status
                order.order_status = 'Cancelled'
                order.is_cancelled = True
                order.canceled_date = timezone.now()
                order.cancel_description = reason
                order.save()
                logger.info(f"Order {order_id} status updated to Cancelled")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Order cancelled successfully and amount refunded to wallet' if order.refund_amount else 'Order cancelled successfully'
                })
                
            else:
                logger.info(f"Order {order_id} with status {order.order_status} cannot be cancelled")
                return JsonResponse({
                    'success': False,
                    'message': f'Orders with status "{order.order_status}" cannot be cancelled'
                })
                
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found for user {request.user.id}")
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            })
        except json.JSONDecodeError:
            logger.error("Invalid JSON data in request")
            return JsonResponse({
                'success': False,
                'message': 'Invalid request data'
            })
        except Exception as e:
            logger.error(f"ERROR IN CANCEL_ORDER: {str(e)}\n{traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': f"An error occurred: {str(e)}"
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


@transaction.atomic
@login_required
def cancel_order_item(request, item_id):
    if request.method == 'POST':
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            data = json.loads(request.body)
            reason = data.get('reason', '')
            
            order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
            order = order_item.order
            
            if order.order_status == 'Shipped':
                return JsonResponse({
                    'success': False,
                    'message': 'Items in shipped orders cannot be directly cancelled. Please request cancellation for the entire order.'
                })
            elif order.order_status not in ['Pending', 'Processing']:
                return JsonResponse({
                    'success': False,
                    'message': 'Items can only be cancelled for pending or processing orders'
                })
            
            if order.items.count() == 1:
                return JsonResponse({
                    'success': False,
                    'message': 'This is the only item in the order. Please cancel the entire order instead.',
                    'is_last_item': True
                })
            
            item_total = order_item.price * order_item.quantity
            
            # Return stock to inventory
            product_variation = order_item.product_variation
            if product_variation:
                product_variation.stock += order_item.quantity
                product_variation.save()
            
            # Process refund for this item if order was paid
            if order.payment_status == 'PAID' and order.payment_method in ['Razorpay', 'Wallet']:
                logger.info(f"Processing refund for cancelled item in order {order.id}, refund amount: {item_total}")
                
                try:
                    # Get or create user wallet
                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    
                    # Add refund amount to wallet
                    previous_balance = wallet.balance
                    wallet.balance += item_total
                    wallet.save()
                    
                    # Create wallet transaction record
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='refund',
                        transaction_amount=item_total,
                        description=f"Partial refund for item in order #{order.id}",
                    )
                    
                    logger.info(f"Item refund processed. Wallet balance updated from {previous_balance} to {wallet.balance}")
                    
                except Exception as wallet_error:
                    logger.error(f"failed to process item refund: {str(wallet_error)}")
                    # Continue with cancellation even if refund fails
            
            # Mark item as cancelled
            order_item.is_cancelled = True
            order_item.return_reason = reason
            order_item.save()
            
            # Update order total
            previous_total = order.total_amount
            order.total_amount -= item_total
            order.save()
            
            # Log the order total update
            logger.info(f"Order total updated from {previous_total} to {order.total_amount}")
            
            return JsonResponse({
                'success': True,
                'message': 'Item cancelled successfully and amount refunded to wallet' if order.payment_status == 'Completed' else 'Item cancelled successfully',
                'new_total': str(order.total_amount)
            })
            
        except Exception as e:
            logger.error(f"Error cancelling order item {item_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"An error occurred: {str(e)}"
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

# ##############################################################order detail#######################################################################
# Updated order_detail view function with detailed price calculations
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.formatted_id = f"PF-{order.order_date.strftime('%Y%m%d')}-{str(order.id).zfill(4)}"
    
    order_items = order.items.all()
    
    # Calculate original price (list price without any discounts)
    original_price = 0
    product_discount_amount = 0
    
    for item in order_items:
        if not item.is_cancelled:
            # Get the original price if possible (MRP or list price)
            if hasattr(item.product_variation, 'price') and hasattr(item.product_variation, 'mrp'):
                # Calculate per item original price and discount
                item_original = item.product_variation.mrp * item.quantity
                item_actual = item.price * item.quantity
                
                original_price += item_original
                product_discount_amount += max(0, item_original - item_actual)
            else:
                # If we can't get the original price, just use the item price
                original_price += item.price * item.quantity
    
    # Calculate subtotal (after product-level discounts but before cart discounts)
    subtotal = sum(item.total_price for item in order_items if not item.is_cancelled)
    
    # Get cart-level discount amount (coupon/offer)
    discount_amount = 0
    if order.discount_amount:
        discount_amount = order.discount_amount
    elif order.cart:
        discount_amount = order.cart.applied_discount
    
    # Get VAT/tax amount
    tax_amount = 0
    if order.vat_amount:
        tax_amount = order.vat_amount
    elif order.cart:
        tax_amount = order.cart.stored_vat_amount
    
    # Calculate grand total (what the customer actually paid)
    grand_total = subtotal - discount_amount + tax_amount
    
    # Calculate total savings
    total_savings = product_discount_amount + discount_amount
    
    # Get coupon code
    coupon_code = None
    if order.cart and order.cart.applied_coupon:
        coupon_code = order.cart.applied_coupon
    
    total_items = sum(item.quantity for item in order_items if not item.is_cancelled)
    active_items_count = order_items.filter(is_cancelled=False).count()
    
    shipping_address = order.shipping_address
    has_tracking = False
    
    context = {
        'order': order,
        'order_items': order_items,
        'total_items': total_items,
        'active_items_count': active_items_count,
        'shipping_address': shipping_address,
        'has_tracking': has_tracking,
        'current_brand': None,
        'order_status': order.order_status,
        'cancel_request_status': order.cancel_request_status,
        'return_status': order.return_status,
        'original_price': original_price,
        'product_discount_amount': product_discount_amount,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'tax_amount': tax_amount,
        'total_savings': total_savings,
        'coupon_code': coupon_code,
        'grand_total': grand_total,  # Add the calculated grand total to the context
    }
    
    return render(request, 'order_detail.html', context)


@login_required
@require_POST
def request_return(request, order_id):
    print("Request return received for order:", order_id)
    print("Request method:", request.method)
    if request.method == "POST":
        try:
            print("Body:", request.body)
            data = json.loads(request.body)
            print("Data parsed:", data)
        except Exception as e:
            print("Error parsing body:", str(e))

    try:
        
        data = json.loads(request.body)
        reason = data.get('reason', '')
        
        if not reason:
            return JsonResponse({
                'success': False,
                'message': 'Return reason is required'
            })
        
        
        order = get_object_or_404(Order, id=order_id, user=request.user)
       
        if order.order_status != 'Delivered':
            return JsonResponse({
                'success': False,
                'message': 'Only delivered orders can be returned'
            })
        
        
        return_window_days = 30  
        if order.days_since_order > return_window_days:
            return JsonResponse({
                'success': False,
                'message': f'Return window has expired (must return within {return_window_days} days of delivery)'
            })
        
       
        if order.return_status:
            return JsonResponse({
                'success': False,
                'message': 'Return has already been requested for this order'
            })
        
        
        order.return_status = Order.RETURN_REQUESTED
        order.return_request_date = timezone.now()
        order.return_reason = reason
        order.save()
        
        
        return JsonResponse({
            'success': True,
            'message': 'Return request submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error requesting return for order {order_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        })

@login_required
@require_POST
def request_item_return(request, item_id):
    try:
        data = json.loads(request.body)
        reason = data.get('reason', '')

        if not reason:
            return JsonResponse({
                'success': False,
                'message': 'Return reason is required'
            })

        item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
        order = item.order

        if order.order_status != 'Delivered':
            return JsonResponse({
                'success': False,
                'message': 'Only items from delivered orders can be returned'
            })

        return_window_days = 30
        if order.days_since_order > return_window_days:
            return JsonResponse({
                'success': False,
                'message': f'Return window has expired (must return within {return_window_days} days  of delivery)'
            })

        if item.return_status:
            return JsonResponse({
                'success': False,
                'message': 'Return has already been requested for this item'
            })

        item.return_status = OrderItem.RETURN_REQUESTED
        item.return_reason = reason
        item.save()

        return JsonResponse({
            'success': True,
            'message': 'Return request submitted successfully',
            'reason': reason
        })

    except Exception as e:
        logger.error(f"Error requesting return for item {item_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        })


from decimal import Decimal, ROUND_HALF_UP

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Format order ID
    order.formatted_id = f"PF-{order.order_date.strftime('%Y%m%d')}-{str(order.id).zfill(4)}"
    
    # Get order items (only non-cancelled ones)
    order_items = order.items.filter(is_cancelled=False)
    
    # Get shipping address
    shipping_address = order.shipping_address
    
    # For the invoice context, prepare all necessary calculations with proper rounding
    current_subtotal = order.current_subtotal
    
    # Calculate proportional discount and VAT with proper rounding
    if order.subtotal > 0:
        remaining_ratio = current_subtotal / order.subtotal
        current_discount = (order.discount_amount * remaining_ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        current_discount = Decimal('0.00')
        
    if order.vat_amount > 0 and order.subtotal > 0:
        vat_rate = order.vat_amount / order.subtotal
        current_vat = (current_subtotal * vat_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        current_vat = Decimal('0.00')
    
    # Calculate final grand total with proper rounding
    current_grand_total = (current_subtotal - current_discount + current_vat).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    context = {
        'order': order,
        'order_items': order_items,
        'shipping_address': shipping_address,
        'company_name': "Cyan Essence",
        'company_address': "123 Fragrance Street, Scent City",
        'company_phone': "+1 234 567 8900",
        'company_email': "info@perfumefusion.com",
        'current_year': datetime.now().year,
        # Add these for the template to use instead of the order fields (with proper rounding)
        'current_subtotal': current_subtotal,
        'current_discount': current_discount,
        'current_vat': current_vat,
        'current_grand_total': current_grand_total
    }
    
    # Render the template
    template = get_template('invoice.html')
    html = template.render(context)
    
    # Create a PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order.formatted_id}.pdf"'
    
    # Define a proper link_callback function
    def link_callback(uri, rel):
        """
        Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
        """
        # Strip static URL if present
        if uri.startswith(settings.STATIC_URL):
            path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
        elif uri.startswith(settings.MEDIA_URL):
            path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        else:
            # Handle case for Google Fonts and other external resources
            return uri
            
        # Make sure that file exists
        if not os.path.isfile(path):
            print(f"Warning: File not found: {path}")
            return uri
            
        return path
    
    # Generate PDF with error handling
    try:
        pisa_status = pisa.CreatePDF(
            html, 
            dest=response,
            encoding='UTF-8',
            link_callback=link_callback
        )
        
        # If error then show some detailed error information
        if pisa_status.err:
            return HttpResponse(f'We had some errors generating the PDF: {pisa_status.err}')
        
        return response
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(f'PDF generation error: {str(e)}<br><pre>{error_details}</pre>')

@login_required(login_url='login')
def validate_password_strength(password):
    """
    Validate that the password meets the minimum requirements
    """
    
    if len(password) < 8:
        return False
    
    
    if not re.search(r'[a-z]', password):
        return False
    
   
    if not re.search(r'\d', password):
        return False
    
  
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True

@login_required(login_url='login')
def mypassword(request):
    if request.method == "POST":
       
        current_password = request.POST.get('current-password')
        new_password = request.POST.get('new-password')
        confirm_password = request.POST.get('confirm-password')
        
        user = request.user
        
        # Check if current password is correct
        if not check_password(current_password, user.password):
            messages.error(request, "Current password is incorrect.")
            return render(request, 'mypassword.html')
        
        # Check if new password is the same as current password
        if check_password(new_password, user.password):
            messages.error(request, "New password cannot be the same as your current password.")
            return render(request, 'mypassword.html')
        
        # Check if passwords match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return render(request, 'mypassword.html')
        
        # Check password strength
        if not validate_password_strength(new_password):
            messages.error(request, "Password must:\n- Be at least 8 characters long\n- Contain at least one lowercase letter\n- Contain at least one number\n- Contain at least one special character")
            return render(request, 'mypassword.html')
        
        
        user.set_password(new_password)
        user.save()
        
        
        update_session_auth_hash(request, user)
        
        messages.success(request, "Password updated successfully!")
        return redirect('mypassword')

    return render(request, 'mypassword.html')


# ######################################################add money###########################################################
@login_required(login_url='login')
def add_money(request):
    try:
        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': 0.00}
        )
        context = {
            'wallet': wallet,
        }
        return render(request, 'myaccount.html', context)
    except Exception as e:
        logger.error(f"Error in add_money view: {str(e)}")
        messages.error(request, "An error occurred while loading your wallet")
        return redirect('myaccount')

@login_required(login_url='login')
def create_razorpay_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')  # Amount in paise

            # Convert to integer for validation
            amount_int = int(amount) if amount else 0
            
            # Update validation to match frontend (10-10000 rupees)
            if not amount or amount_int < 1000 or amount_int > 1000000:
                return JsonResponse({'error': f'Invalid amount: {amount_int} paise. Must be between 1000-1000000 paise (₹10-₹10000)'}, status=400)
            
            order_currency = 'INR'
            order_receipt = f'order_rcptid_{request.user.id}_{timezone.now().timestamp()}'

            # Make sure razorpay_client is properly initialized
            razorpay_order = razorpay_client.order.create({
                'amount': amount_int,  # Ensure it's an integer
                'currency': order_currency,
                'receipt': order_receipt,
                'payment_capture': 1,  # Auto capture
            })
            
            # Change first_name and last_name to firstname and lastname
            return JsonResponse({
                'order_id': razorpay_order['id'],
                'amount': amount_int,
                'currency': order_currency,
                'key_id': settings.RAZORPAY_KEY_ID,
                'user_name': f"{request.user.firstname} {request.user.lastname}",  # FIXED HERE
                'email': request.user.email,
                'phone': request.user.phonenumber  # CHANGED HERE to use built-in field
            })
            
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required(login_url='login')
def verify_payment(request):
    if request.method == "POST":
        try:
            print("Verify payment request:", request.body)
            # Parse JSON data from request body
            data = json.loads(request.body)
            print("Parsed verification data:", data)


            # Get payment data
            payment_id = data.get('razorpay_payment_id')
            order_id = data.get('razorpay_order_id')
            signature = data.get('razorpay_signature')
            amount = data.get('amount')  # Amount in rupees
            
            print(f"Payment details: ID={payment_id}, Order={order_id}, Amount={amount}")

            # Check if this payment was already processed
            if WalletTransaction.objects.filter(description__contains=payment_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Payment already processed'
                }, status=400)
            
            # Verify payment signature
            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            }
            
            # Verify the payment signature
            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
                payment_verified = True
               
            except Exception as e:
                payment_verified = False
                
            if payment_verified:
                # Add money to user's wallet
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                previous_balance = wallet.balance
                wallet.balance += Decimal(amount)
                wallet.save()
                
                # Create transaction record with payment ID in description
                description = f"Added money to wallet - Payment ID: {payment_id}"
                transaction = WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_amount=amount,
                    transaction_type='add',  # Using your existing transaction type
                    description=description,
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Payment successful',
                    'amount': amount,
                    'transaction_id': transaction.id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Payment verification failed'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)