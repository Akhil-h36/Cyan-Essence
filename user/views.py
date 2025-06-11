from adminapp.models import (
    ProductTable, 
    BrandTable, 
    Gender, 
    Occasion, 
    Fragrance, 
    ConcentrationType,
    SizeTable,
    Cart, CartItem,
    VarienceTable,
    Wishlist,
    coupon,
    WalletTransaction,
    Wallet,
    review,
    OfferTable
)
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_GET

from decimal import Decimal
from django.utils import timezone

current_time = timezone.now()

from django.utils import timezone
import razorpay
from django.conf import settings
from adminapp.models import ProductTable, ProductImage, VarienceTable
from userprofile.models import UserAddress
from .models import Order ,OrderItem
from datetime import timedelta
from django.shortcuts import render,redirect
from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import  get_object_or_404
from django.db.models import Avg, Q
from django.db.models import Min, F, Value, FloatField
from django.db import transaction
from django.core .paginator import PageNotAnInteger,Paginator,EmptyPage
import logging
import traceback
logger = logging.getLogger(__name__)
from django.db.models import Q, Min
from django.db.models import Sum

# Create your views here.


def nohome(request):
    
    latest_products = ProductTable.objects.filter(
        is_active=True,  
    ).order_by('-product_id')[:3] 
    
    
    featured_products = ProductTable.objects.filter(
        is_active=True
    ).order_by('?')[:3]  
    
    
    for product in latest_products:
        
        product.display_variance = product.varience.order_by('size__size').first()
    
    for product in featured_products:
        
        product.display_variance = product.varience.order_by('size__size').first()
    
    # Prepare context data
    context = {
        'latest_products': latest_products,
        'featured_products': featured_products
    }
    
    return render(request, 'noHome.html', context)


def best_selling_products3(limit=10):
    """
    Get the best selling products
    """
    
    best_products = OrderItem.objects.values(
        'product_variation__product__product_id',  # Adjusted to use product_id from ProductTable
        'product_variation__product__product_name'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:limit]
    
    result = []
    for i, product in enumerate(best_products, 1):
        product_id = product['product_variation__product__product_id']
        try:
            product_obj = ProductTable.objects.get(product_id=product_id)
            
            image = product_obj.images.first()
            image_url = image.image.url if image else None
        except ProductTable.DoesNotExist:
            image_url = None
            
        result.append({
            'rank': i,
            'product_id': product_id,  # Add product_id to the result dictionary
            'name': product['product_variation__product__product_name'],
            'total_sold': product['total_sold'],
            'image_url': image_url
        })
    
    return result

from django.views.decorators.cache import never_cache

@never_cache
@login_required(login_url='login')
def home(request):
    brands = BrandTable.objects.all()
    top_products =best_selling_products3(limit=3)
    
    return render(request,'Home.html', {'brands': brands,'top_products' : top_products})




def myshop(request):
    products = ProductTable.objects.filter(is_active=True).prefetch_related('images', 'varience')
    brand_filters = request.GET.getlist('brand')
    gender_filters = request.GET.getlist('gender')
    occasion_filters = request.GET.getlist('occasion')
    fragrance_filters = request.GET.getlist('fragrance')
    concentration_filters = request.GET.getlist('concentration')
    
    size_filters = request.GET.get('size', '').split(',')
    size_filters = [int(size) for size in size_filters if size.strip()]

    brand_search = request.GET.get('brand_search', '').strip()
    if brand_search:
        products = products.filter(brand__brand_name__icontains=brand_search)

    min_price = request.GET.get('min_price', 500)
    max_price = request.GET.get('max_price', 30000)
    
    sort_by = request.GET.get('sort_by', 'default')

    # Build the base filter query
    filter_query = Q()
    
    if brand_filters:
        filter_query |= Q(brand__brand_name__in=brand_filters)
    
    if gender_filters:
        filter_query |= Q(gender__gender__in=gender_filters)
    
    if occasion_filters:
        filter_query |= Q(occasion__occasion__in=occasion_filters)
    
    if fragrance_filters:
        filter_query |= Q(fragrance__fragrance_type__in=fragrance_filters)
    
    if concentration_filters:
        filter_query |= Q(concentration__concentration__in=concentration_filters)
    
    if brand_filters or gender_filters or occasion_filters or fragrance_filters or concentration_filters:
        products = products.filter(filter_query)

    # Apply price filters globally
    products = products.filter(
        varience__price__gte=float(min_price),
        varience__price__lte=float(max_price)
    )

    from django.db.models import Min, F, Case, When
    
    if size_filters:
        
        products = products.filter(varience__size__size__in=size_filters)
        products = products.annotate(
            filtered_min_price=Min('varience__price', filter=Q(varience__size__size__in=size_filters))
        )
        
        
        products = products.annotate(
            filtered_variance_id=Min(
                'varience__id',
                filter=Q(varience__size__size__in=size_filters)
            )
        )
    else:
        logger.info("No size filters, using overall minimum price")
        # If no size filter, annotate with the overall minimum price and first variance ID
        products = products.annotate(
            filtered_min_price=Min('varience__price'),
            filtered_variance_id=Min('varience__id')
        )

    # Apply sorting
    if sort_by == 'price_low_to_high':
        products = products.order_by('filtered_min_price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-filtered_min_price')
    elif sort_by == 'name_asc':
        products = products.order_by('product_name')
    elif sort_by == 'name_desc':
        products = products.order_by('-product_name')

    # Make sure we only get distinct products
    products = products.distinct()


    products_per_page = 10 
    paginator = Paginator(products, products_per_page)  

    page = request.GET.get('page', 1)  

    try:
        paginated_products = paginator.page(page)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)

    curret_time = timezone.now()
    for product in paginated_products:

        try:
            if hasattr(product, 'filtered_variance_id') and product.filtered_variance_id:
                variance = VarienceTable.objects.get(id=product.filtered_variance_id)
                product.original_price = variance.price
                product.discounted_price = variance.get_final_price()

                if product.discounted_price < product.original_price:
                    product.has_discount = True
                    product.discount_amount = product.original_price - product.discounted_price
                    product.discount_percentage = (product.discount_amount / product.original_price) * 100

                    product_offer = product.product_offers.filter(
                        is_active=True,
                        valid_from__lte=current_time,
                        valid_to__gte=current_time
                    ).first()
                    
                    brand_offer = product.brand.brand_offers.filter(
                        is_active=True,
                        valid_from__lte=current_time,
                        valid_to__gte=current_time
                    ).first()

                    if product_offer and brand_offer:
                        product_discount = product_offer.calculate_discounted_price(product.original_price)
                        brand_discount = brand_offer.calculate_discounted_price(product.original_price)
                        
                        if product_discount <= brand_discount:
                            product.applied_offer = product_offer
                        else:
                            product.applied_offer = brand_offer
                    elif product_offer:
                        product.applied_offer = product_offer
                    elif brand_offer:
                        product.applied_offer = brand_offer
                else:
                    product.has_discount = False
                    product.applied_offer = None
        except VarienceTable.DoesNotExist:
            product.has_discount = False
            product.discounted_price = product.filtered_min_price
            product.applied_offer = None



    # Prepare filter options for the template
    filter_options = {
        'brands': BrandTable.objects.all(),
        'genders': Gender.objects.all(),
        'occasions': Occasion.objects.all(),
        'fragrances': Fragrance.objects.all(),
        'concentrations': ConcentrationType.objects.all(),
        'sizes': SizeTable.objects.all(),
    }

    context = {
        'products': paginated_products,
        'filter_options': filter_options,
        'selected_filters': {
            'brands': brand_filters,
            'genders': gender_filters,
            'occasions': occasion_filters,
            'fragrances': fragrance_filters,
            'concentrations': concentration_filters,
            'sizes': size_filters,
            'min_price': min_price,
            'max_price': max_price,
            'sort_by': sort_by
        },
        'brand_search': brand_search,
        'has_size_filter': bool(size_filters),
        'page_obj': paginated_products,
    }
    return render(request, 'myshop.html', context)


@never_cache
def singleproduct(request, product_id):
    try:
        # First get the product - this needs to happen BEFORE accessing product.reviews
        product = get_object_or_404(
            ProductTable.objects.select_related(
                'brand', 'gender', 'occasion', 
                'fragrance', 'concentration'
            ).prefetch_related(
                'images', 'varience__size'
            ),
            pk=product_id
        )
        
        try:
            avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
            reviews = product.reviews.all().order_by('-created_at')
            selected_size = int(request.GET.get('size', '0'))
        except (ValueError, TypeError):
            avg_rating = 0  # Default rating if no reviews
            reviews = []    # Empty list for no reviews
            selected_size = 0

        # Get all images
        all_images = product.images.all()
        main_image = all_images[0] if all_images else None
        other_images = list(all_images[1:])  

        variances = product.varience.all().order_by('price')
        
        # Process discounts for all variances
        current_time = timezone.now()
        for variance in variances:
            variance.original_price = variance.price
            variance.final_price = variance.get_final_price()
            variance.has_discount = variance.final_price < variance.original_price
            
            if variance.has_discount:
                variance.discount_amount = variance.original_price - variance.final_price
                variance.discount_percentage = (variance.discount_amount / variance.original_price) * 100
                
                # Get the applied offer information
                product_offer = product.product_offers.filter(
                    is_active=True,
                    valid_from__lte=current_time,
                    valid_to__gte=current_time
                ).first()
                
                brand_offer = product.brand.brand_offers.filter(
                    is_active=True,
                    valid_from__lte=current_time,
                    valid_to__gte=current_time
                ).first()
                
                if product_offer and brand_offer:
                    product_discount = product_offer.calculate_discounted_price(variance.original_price)
                    brand_discount = brand_offer.calculate_discounted_price(variance.original_price)
                    
                    if product_discount <= brand_discount:
                        variance.applied_offer = product_offer
                    else:
                        variance.applied_offer = brand_offer
                elif product_offer:
                    variance.applied_offer = product_offer
                elif brand_offer:
                    variance.applied_offer = brand_offer
        
        default_variance = None
        if selected_size:
            default_variance = variances.filter(size__size=selected_size).first()
        if not default_variance:
            default_variance = variances.first()

        # Check if product is in user's wishlist
        in_wishlist = False
        wishlist_items = []
        if request.user.is_authenticated:
            wishlist_items = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
            in_wishlist = product.product_id in wishlist_items

        # Get related products
        related_products = ProductTable.objects.filter(
            brand=product.brand,  
            is_active=True       
        ).exclude(pk=product_id).annotate(
            min_price=Min('varience__price')
        ).order_by('min_price')[:8]  

        # Process discounts for related products
        for related_product in related_products:
            min_variance = related_product.varience.order_by('price').first()
            if min_variance:
                related_product.original_price = min_variance.price
                related_product.final_price = min_variance.get_final_price()
                related_product.has_discount = related_product.final_price < related_product.original_price

        if related_products.count() < 8:
            additional_products = ProductTable.objects.filter(
                Q(gender=product.gender) | 
                Q(occasion=product.occasion) |
                Q(fragrance=product.fragrance),
                is_active=True
            ).exclude(
                Q(pk=product_id) |
                Q(pk__in=[p.pk for p in related_products]) 
            ).annotate(
                min_price=Min('varience__price')
            ).order_by('min_price')[:8 - related_products.count()]
            
            # Process discounts for additional products
            for additional_product in additional_products:
                min_variance = additional_product.varience.order_by('price').first()
                if min_variance:
                    additional_product.original_price = min_variance.price
                    additional_product.final_price = min_variance.get_final_price()
                    additional_product.has_discount = additional_product.final_price < additional_product.original_price
                    
            # Combine querysets
            related_products = list(related_products) + list(additional_products)

        # Prepare context
        context = {
            'reviews': reviews,
            'avg_rating': avg_rating if avg_rating else 0,
            'product': product,
            'main_image': main_image,
            'other_images': other_images,
            'variances': variances,
            'default_variance': default_variance,
            'related_products': related_products,
            'is_available': not product.isOutOfStock,
            'stock_status': 'In Stock' if not product.isOutOfStock else 'Out of Stock',
            'selected_size': selected_size if selected_size else default_variance.size.size if default_variance else None,
            'current_brand': product.brand,
            'in_wishlist': in_wishlist,
            'wishlist_items': wishlist_items  # Pass the list of wishlist product IDs
        }

        return render(request, 'singleproduct.html', context)

    except Exception as e:
        logger.error(f"Error loading product {product_id}: {str(e)}\n{traceback.format_exc()}")
        
        # Fallback with minimal data
        product = get_object_or_404(ProductTable, pk=product_id)
        return render(request, 'singleproduct.html', {
            'product': product,
            'error_message': "Some product details couldn't be loaded",
            'current_brand': product.brand if product else None,
            'in_wishlist': False,
            'wishlist_items': []
        })

@login_required
def submit_review(request, product_id):
    if request.method == 'POST':
        try:
            product = ProductTable.objects.get(pk=product_id)
            rating = int(request.POST.get('rating'))
            review_text = request.POST.get('review_text')
            
            # Create or update review
            review_obj, created = review.objects.update_or_create(
                user=request.user,
                product=product,
                defaults={
                    'rating': rating,
                    'review_text': review_text
                }
            )
            
            # Return response with appropriate user data
            return JsonResponse({
                'success': True,
                'message': 'Review submitted successfully!',
                'review': {
                    'username': request.user.get_full_name(),
                    'created_at': review_obj.created_at.strftime("%B %d, %Y"),
                    'rating': review_obj.rating,
                    'review_text': review_obj.review_text
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)


@require_GET
def get_product_reviews(request, product_id):
    try:
        reviews = review.objects.filter(product_id=product_id).order_by('-created_at')
        reviews_data = []
        
        for rev in reviews:
            reviews_data.append({
                'id': rev.id,  # Fixed: Changed from review.id to rev.id
                'username': rev.user.get_full_name(),  # Fixed: Changed from review.user.username to rev.user.get_full_name()
                'rating': rev.rating,  # Fixed: Changed from review.rating to rev.rating
                'review_text': rev.review_text,  # Fixed: Changed from review.review_text to rev.review_text
                'created_at': rev.created_at.strftime('%B %d, %Y')  # Fixed: Changed from review.created_at to rev.created_at
            })
        
        return JsonResponse({
            'success': True,
            'reviews': reviews_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required(login_url='login')
def cart(request):

    cart, created = Cart.objects.get_or_create(user=request.user)
    
    
    cart_items = cart.items.select_related('product', 'variance', 'product__brand', 'variance__size').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items
    }
    return render(request, 'cart.html', context)

@require_POST
@login_required
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        variance_id = data.get('variance_id')
        quantity = int(data.get('quantity', 1))
        
        logger.info(f"Adding to cart: product_id={product_id}, variance_id={variance_id}, quantity={quantity}")
        
        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Check if the cart was newly created or if it might have stale values
        # If there are no items but discount/VAT values exist, reset them
        if created or (cart.items.count() == 0 and 
                      (cart.applied_discount > Decimal('0.00') or 
                       cart.stored_vat_amount > Decimal('0.00') or 
                       cart.applied_coupon)):
            # Reset any potential stale values
            logger.info(f"Resetting cart values for user {request.user.id} (new cart or empty with values)")
            cart.applied_discount = Decimal('0.00')
            cart.applied_coupon = None
            cart.stored_vat_amount = Decimal('0.00')
            cart.save()
   
        try:
            product = ProductTable.objects.get(pk=product_id)
            variance = VarienceTable.objects.get(id=variance_id)
            
            # Check stock
            if int(variance.stock) < int(quantity):
                return JsonResponse({
                    'success': False,
                    'message': 'Not enough items in stock'
                })
            
            # Get or create cart item
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variance=variance,
                defaults={'quantity': quantity}
            )
            
            # If item already exists, update quantity
            if not item_created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Product added to cart successfully',
                'cart_count': cart.total_items
            })
        except ProductTable.DoesNotExist:
            logger.error(f"Product not found: {product_id}")
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            })
        except VarienceTable.DoesNotExist:
            logger.error(f"Variance not found: {variance_id}")
            return JsonResponse({
                'success': False,
                'message': 'Product variance not found'
            })
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format'
        })
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f"An error occurred try login: {str(e)}"
        })
    
@require_POST
@login_required
def update_cart_item(request):
    data = json.loads(request.body)
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))
    
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        
       
        if quantity > cart_item.variance.stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {cart_item.variance.stock} items available in stock'
            })
        
        cart_item.quantity = quantity
        cart_item.save()
        
        
        cart = cart_item.cart
        
        return JsonResponse({
            'success': True,
            'item_total': float(cart_item.total_price),
            'cart_subtotal': float(cart.total_price),
            'cart_discount': float(cart.applied_discount),
            'cart_vat': float(cart.vat_amount),
            'cart_total': float(cart.final_total),
            'cart_count': cart.total_items  
        })
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found in your cart'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
    

@require_GET
@login_required
def get_product_stock(request):
    """
    Get the current stock for a cart item
    """
    try:
        item_id = request.GET.get('item_id')
        
        if not item_id:
            return JsonResponse({'success': False, 'message': 'Item ID is required'})
        
        # Get the cart item
        cart_item = CartItem.objects.select_related('variance').get(
            id=item_id, 
            cart__user=request.user
        )
        
        # Return the stock information
        return JsonResponse({
            'success': True,
            'stock': cart_item.variance.stock,
            'item_id': item_id
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
@login_required
def remove_cart_item(request):
    data = json.loads(request.body)
    item_id = data.get('item_id')
    
    try:
        cart_item = CartItem.objects.get(pk=item_id, cart__user=request.user)
        cart_item.delete()
        
       
        cart = Cart.objects.get(user=request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': cart.total_items,
            'cart_subtotal': float(cart.total_price),
            'cart_discount': float(cart.applied_discount),
            'cart_vat': float(cart.vat_amount),
            'cart_total': float(cart.final_total)
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def get_cart_count(request):
    try:
        cart = Cart.objects.get(user=request.user)
        return JsonResponse({'success': True, 'cart_count': cart.total_items})
    except Cart.DoesNotExist:
        return JsonResponse({'success': True, 'cart_count': 0})

@never_cache
@login_required
def checkout(request):
    cart =Cart.objects.get(user=request.user)
    cart_items= cart.items.all()
    addresses=UserAddress.objects.filter(user=request.user)

    subtotal =cart.total_price
    discount=cart.applied_discount
    vat= cart.vat_amount
    total=cart.final_total
    
    wallet_balance = 0
    try:
        wallet = Wallet.objects.get(user=request.user)
        wallet_balance = wallet.balance
    except Wallet.DoesNotExist:
        # Create a wallet for the user if it doesn't exist
        wallet = Wallet.objects.create(user=request.user)
        wallet_balance = 0

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'addresses': addresses,
        'subtotal': subtotal,
        'discount': discount,
        'vat': vat,
        'total': total,
        'wallet_balance': wallet_balance,
    }

    return render(request, 'checkout.html', context)




@never_cache
@login_required
@transaction.atomic
def place_order(request):
    if request.method == 'POST':
        try:
            # Parse request data
            data = json.loads(request.body)
            address_id = data.get('address_id')
            payment_method = data.get('payment_method')
            
            # Debug logging
            logger.info(f"Starting order placement for user {request.user.id}, payment method: {payment_method}")
            
            # Get user's cart
            try:
                cart = Cart.objects.get(user=request.user)
                cart_items = cart.items.all()
                
                if not cart_items.exists():
                    return JsonResponse({'success': False, 'message': 'Your cart is empty'})
            except Cart.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Cart not found'})

            
            try:
                address = UserAddress.objects.get(address_id=address_id, user=request.user)
            except UserAddress.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid address selected'})
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid address ID format'})
            

            if payment_method == 'COD' and cart.final_total > 5000:
                return JsonResponse({
                    'success': False,
                    'message': 'Cash on Delivery is not available for orders above ₹5000'
                })




            delivery_address = {
                'full_name': address.full_name,
                'phone_number': address.phone_number,
                'address_line1': address.address_line1,
                'address_line2': address.address_line2,
                'city': address.city,
                'state': address.state,
                'postal_code': address.postal_code
            }

            # Create order
            order = Order.objects.create(
                user=request.user,
                cart=cart,
                total_amount=cart.final_total,
                shipping_address=address,
                delivery_address=json.dumps(delivery_address),
                payment_method=payment_method,
                payment_status='Pending'
            )

            # Create order items
            for cart_item in cart_items:

                OrderItem.objects.create(
                    order=order,
                    product_variation=cart_item.variance,
                    quantity=cart_item.quantity,
                    price=cart_item.total_price,
                )
            
            

            # Process wallet payment if selected
            if payment_method == 'Wallet':
                try:
                    wallet = Wallet.objects.get(user=request.user)
                    
                    if wallet.balance >= cart.final_total:
                        wallet.balance -= cart.final_total
                        wallet.save()
                        
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_type='deduct',
                            transaction_amount=cart.final_total,
                            description=f'Payment for Order #{order.id}'
                        )
                        
                        order.payment_status = 'PAID'
                        order.save()
                        
                        # Clear cart items
                        cart_items.delete()
                        
                        # Reset coupon information after order completion
                        reset_cart(cart)
                        
                        return JsonResponse({
                            'success': True,
                            'order_id': order.id,
                            'message': 'Order placed successfully using wallet balance'
                        })
                    else:
                        # Insufficient balance
                        order.payment_status = 'failed'
                        order.save()
                        
                        return JsonResponse({
                            'success': False,
                            'error': 'Insufficient wallet balance. Please add money to your wallet or choose a different payment method.'
                        })
                except Wallet.DoesNotExist:
                    # Wallet doesn't exist
                    order.payment_status = 'failed'
                    order.save()
                    
                    return JsonResponse({
                        'success': False,
                        'error': 'Wallet not found. Please choose a different payment method.'
                    })
            
            elif payment_method == 'Razorpay':
                try:
                    logger.info("Initializing Razorpay client")
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    
                    amount_in_paise = int(cart.final_total * 100)
                    logger.info(f"Creating Razorpay order for amount: {amount_in_paise} paise")
                    
                    # Validate amount - Razorpay minimum is 100 paise (₹1)
                    if amount_in_paise < 100:
                        logger.error(f"Amount too small for Razorpay: {amount_in_paise} paise")
                        order.payment_status = 'failed'
                        order.save()
                        return JsonResponse({
                            'success': False,
                            'message': 'Amount too small for online payment. Minimum is ₹1.',
                            'error': 'Amount too small'
                        })
                    
                    # Create Razorpay order
                    razorpay_order = client.order.create({
                        'amount': amount_in_paise,
                        'currency': 'INR',
                        'receipt': f'order_{order.id}',
                        'payment_capture': '1',
                        'notes': {
                            'order_id': str(order.id),
                            'user_id': str(request.user.id)
                        }
                    })
                    logger.info(f"Razorpay order created: {razorpay_order['id']}")

                    # Update order with Razorpay order ID
                    order.razorpay_order_id = razorpay_order['id']
                    order.save()

                    # Prepare payment data for frontend
                    payment_data = {
                        'key_id': settings.RAZORPAY_KEY_ID,
                        'amount': amount_in_paise,
                        'currency': 'INR',
                        'order_id': razorpay_order['id'],
                        'name': request.user.get_full_name() or request.user.username,
                        'email': request.user.email,
                        'contact': address.phone_number,
                        'description': f'Order #{order.id}',
                        'prefill': {
                            'name': request.user.get_full_name() or request.user.username,
                            'email': request.user.email,
                            'contact': address.phone_number
                        },
                        'notes': {
                            'order_id': str(order.id)
                        },
                        'theme': {'color': '#3399cc'}
                    }

                    # At this point, we don't clear the cart yet since payment is pending

                    return JsonResponse({
                        'success': True,
                        'order_id': order.id,
                        'payment_data': payment_data,
                        'message': 'Redirecting to payment gateway'
                    })

                except razorpay.errors.BadRequestError as e:
                    logger.error(f"Razorpay BadRequestError: {str(e)}")
                    order.payment_status = 'failed'
                    order.save()
                    return JsonResponse({
                        'success': False,
                        'message': 'Payment gateway error. Please try another method.',
                        'error': str(e)
                    })
                except Exception as e:
                    logger.error(f"Razorpay error: {str(e)}\n{traceback.format_exc()}")
                    order.payment_status = 'failed'
                    order.save()
                    return JsonResponse({
                        'success': False,
                        'message': 'Payment processing error. Please try again.',
                        'error': str(e)
                    })
            else:
                # For COD or other non-online payment methods
                cart_items.delete()
                
                # Reset coupon information after order completion
                reset_cart(cart)
                
                return JsonResponse({
                    'success': True,
                    'order_id': order.id,
                    'message': 'Order placed successfully'
                })
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({'success': False, 'error': 'Invalid request format'})
        except Exception as e:
            logger.error(f"Unexpected error in place_order: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Helper function to reset cart values
def reset_cart(cart):
    """Reset cart discount and tax values after order completion"""
    cart.applied_discount = Decimal('0.00')
    cart.applied_coupon = None
    cart.stored_vat_amount = Decimal('0.00')
    cart.save()
    logger.info(f"Cart values reset for user {cart.user.id}")
# #################################################################################################################
  
def razorpay_callback(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            }
            
            # Find our order with this Razorpay order ID
            try:
                order = Order.objects.get(razorpay_order_id=order_id)
            except Order.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Order not found'})
            
            # Verify payment signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            try:
                client.utility.verify_payment_signature(params_dict)
                # Payment successful
                order.payment_status = 'PAID'
                order.save()
                # Clear cart items here if needed
                
                return JsonResponse({'status': 'success', 'order_id': order.id})
            except Exception as e:
                # Payment verification failed
                order.payment_status = 'failed'
                order.save()
                return JsonResponse({'status': 'error', 'message': str(e)})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@never_cache
@require_POST
def razorpay_payment_cancel(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            razorpay_order_id = data.get('razorpay_order_id')
            order_id = data.get('order_id')
            
            if razorpay_order_id:
                try:
                    order = Order.objects.get(razorpay_order_id=razorpay_order_id, id=order_id)
                    
                    # Only update if payment is still pending
                    if order.payment_status in ['Pending', 'Retry']:
                        order.payment_status = 'failed'
                        order.save()
                        
                        # Return the retry URL
                        return JsonResponse({
                            'success': True,
                            'order_id': order.id,
                            'redirect_url': reverse('order_confirmation', args=[order.id])
                        })
                    else:
                        # Payment was already processed, can't cancel
                        return JsonResponse({
                            'success': False,
                            'message': 'Payment already processed'
                        })
                except Order.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Order not found'})
            else:
                return JsonResponse({'success': False, 'message': 'No order ID provided'})
                
        except Exception as e:
            logger.error(f"Error processing payment cancellation: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def retry_payment(request, order_id):
    """
    Handle payment retry for failed orders using Razorpay
    """
    try:
        # Get the order, ensuring it belongs to the current user
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Check if this order is eligible for payment retry
        if order.payment_status not in ['failed', 'Pending', 'Retry']:
            messages.error(request, "This order doesn't require payment retry.")
            return redirect('order_detail', order_id=order_id)
        
        # Initialize Razorpay client
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Create a new Razorpay order
            amount_in_paise = int(order.total_amount * 100)
            razorpay_order = client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': f'order_{order.id}_retry',
                'payment_capture': '1',
                'notes': {
                    'order_id': str(order.id),
                    'user_email': request.user.email,
                    'retry': 'true'
                }
            })
            
            # Update the order with new Razorpay ID
            order.razorpay_order_id = razorpay_order['id']
            order.payment_status = 'Retry'
            order.save()
            
            # Get shipping address from order
            shipping_contact = ''
            if hasattr(order, 'shipping_address') and order.shipping_address:
                if hasattr(order.shipping_address, 'phone_number'):
                    shipping_contact = order.shipping_address.phone_number
            
            # Prepare data for the template
            payment_data = {
                'key_id': settings.RAZORPAY_KEY_ID,
                'amount': amount_in_paise,
                'currency': 'INR',
                'order_id': razorpay_order['id'],
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'contact': shipping_contact,
                'description': f'Payment retry for Order #{order.id}',
                'prefill': {
                    'name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                    'contact': shipping_contact
                },
                'notes': {
                    'order_id': str(order.id),
                    'retry': 'true'
                },
                'callback_url': request.build_absolute_uri('/verify-payment/'),
                'theme': {'color': '#3399cc'}
            }
            
            context = {
                'order': order,
                'payment_data': payment_data
            }
            
            return render(request, 'retry_payment.html', context)
            
        except razorpay.errors.BadRequestError as e:
            logger.error(f"Razorpay BadRequestError: {str(e)}")
            messages.error(request, "Payment gateway error. Please try again later.")
            return redirect('order_detail', order_id=order_id)
        
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            messages.error(request, "An error occurred while setting up your payment. Please try again later.")
            return redirect('order_detail', order_id=order_id)
            
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('myorders')

    
 
@require_POST
def verify_payment(request):
    try:
        
        if request.content_type == 'application/x-www-form-urlencoded':
            
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            
            
            try:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            except Order.DoesNotExist:
                logger.error(f"Order not found for Razorpay order ID: {razorpay_order_id}")
                return JsonResponse({'success': False, 'message': 'Order not found'})
        else:
           
            data = json.loads(request.body)
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_signature = data.get('razorpay_signature')
            order_id = data.get('order_id')
            
            
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                
                if order.razorpay_order_id != razorpay_order_id:
                    logger.error(f"Razorpay order ID mismatch: {order.razorpay_order_id} != {razorpay_order_id}")
                    return JsonResponse({'success': False, 'message': 'Order ID mismatch'})
            except Order.DoesNotExist:
                logger.error(f"Order not found for ID: {order_id}")
                return JsonResponse({'success': False, 'message': 'Order not found'})
        
       
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        
        params_dict = {
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            
            client.utility.verify_payment_signature(params_dict)
            order.payment_status = 'PAID'
            order.razorpay_payment_id = razorpay_payment_id
            order.save()
            
        
            if order.cart and order.cart.items.exists():
                order.cart.items.all().delete()
            
           
            if request.content_type == 'application/x-www-form-urlencoded':
               
                return redirect('payment_success', order_id=order.id)
            else:
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Payment verified successfully',
                    'redirect_url': f'/payment-success/{order.id}/'
                })
            
        except Exception as e:
            
            logger.error(f"Payment signature verification failed: {str(e)}")
            order.payment_status = 'failed'
            order.save()
            
            
            if request.content_type == 'application/x-www-form-urlencoded':
                
                return redirect('payment_failed', order_id=order.id)
            else:
                
                return JsonResponse({
                    'success': False, 
                    'message': 'Payment verification failed. You can retry payment from your orders page.',
                    'redirect_url': f'/payment-failed/{order.id}/'
                })
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_POST
def update_address(request):
    try:
        data = json.loads(request.body)
        address_id = data.get('address_id')
        
        if not address_id:
            return JsonResponse({'success': False, 'message': 'Address ID is required'})
        
        try:
           
            address = UserAddress.objects.get(address_id=address_id, user=request.user)
            
        
            address.full_name = data.get('full_name', address.full_name)
            address.phone_number = data.get('phone_number', address.phone_number)
            address.address_line1 = data.get('address_line1', address.address_line1)
            address.address_line2 = data.get('address_line2', address.address_line2)
            address.city = data.get('city', address.city)
            address.state = data.get('state', address.state)
            address.postal_code = data.get('postal_code', address.postal_code)
            address.country = data.get('country', address.country)
            
           
            if not address.full_name or not address.phone_number or not address.address_line1:
                return JsonResponse({'success': False, 'message': 'Required fields are missing'})
            
            
            if len(address.phone_number) < 10 or not address.phone_number.isdigit():
                return JsonResponse({'success': False, 'message': 'Invalid phone number'})

            address.save()
            
            return JsonResponse({'success': True, 'message': 'Address updated successfully'})
        except UserAddress.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Address not found'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating address: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})


def order_status_api(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        return JsonResponse({
            'order_status': order.order_status,
            'payment_status': order.payment_status
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

@login_required
@require_POST
def save_address(request):
    try:
        data = json.loads(request.body)
        address = UserAddress.objects.create(
            user=request.user,
            full_name=data.get('full_name'),
            phone_number=data.get('phone_number'),
            address_line1=data.get('address_line1'),
            address_line2=data.get('address_line2', ''),
            city=data.get('city'),
            state=data.get('state'),
            postal_code=data.get('postal_code'),
            country=data.get('country'),
            is_default=False  # You can implement logic to set default addresses
        )
        return JsonResponse({'success': True, 'message': 'Address saved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# Add these views to your views.py file

@login_required
def get_available_coupons(request):
    """Return a list of available coupons for the current user"""
    if request.method == 'GET':
        # Get current date and time for coupon validation
        now = timezone.now()
        
        # Get cart to check against minimum order values
        try:
            cart = Cart.objects.get(user=request.user)
            cart_total = cart.final_total
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No active cart found'})
        
        # Query for active coupons
        available_coupons = coupon.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        )
        
        # Filter out coupons where the minimum order amount is greater than the cart total
        applicable_coupons = []
        for c in available_coupons:
            if c.min_order_amount is None or cart_total >= c.min_order_amount:
                applicable_coupons.append({
                    'coupon_code': c.coupon_code,
                    'description': c.description,
                    'discount_type': c.discount_type,
                    'discount_value': float(c.discount_value if c.discount_value else 0),
                    'min_order_amount': float(c.min_order_amount if c.min_order_amount else 0),
                    'max_discount_value': float(c.max_discount_value if c.max_discount_value else 0),
                    'valid_from': c.valid_from.isoformat(),
                    'valid_to': c.valid_to.isoformat(),
                    'usage_limit': c.usage_limit
                })
        
        return JsonResponse({
            'success': True,
            'coupons': applicable_coupons
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def apply_coupon(request):
    """Apply a coupon to the user's cart"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            coupon_code = data.get('coupon_code')
            
            if not coupon_code:
                return JsonResponse({'success': False, 'message': 'Coupon code is required'})
            
            # Get the coupon
            try:
                coupon_obj = coupon.objects.get(
                    coupon_code=coupon_code,
                    is_active=True,
                    valid_from__lte=timezone.now(),
                    valid_to__gte=timezone.now()
                )
            except coupon.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid or expired coupon code'})
            
            # Get the cart
            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'No active cart found'})
            
            # Check minimum order amount
            if coupon_obj.min_order_amount and cart.total_price < coupon_obj.min_order_amount:
                return JsonResponse({
                    'success': False, 
                    'message': f'This coupon requires a minimum order of ₹{coupon_obj.min_order_amount}'
                })
            
            # Calculate discount
            discount_amount = 0
            if coupon_obj.discount_type == 'percentage':
                discount_amount = (cart.total_price * coupon_obj.discount_value) / 100
                # Apply max discount limit if set
                if coupon_obj.max_discount_value and discount_amount > coupon_obj.max_discount_value:
                    discount_amount = coupon_obj.max_discount_value
            else:  # fixed amount
                discount_amount = coupon_obj.discount_value
            
            # Update cart with coupon discount
            cart.applied_discount = discount_amount
            cart.applied_coupon = coupon_obj.coupon_code
            
            # Calculate and store VAT amount
            subtotal = cart.total_price
            discount = cart.applied_discount
            vat_amount = (subtotal - discount) * Decimal('0.05')  # 5% VAT
            cart.stored_vat_amount = vat_amount  # Set the stored field
            
            # Save the cart now
            cart.save()
            
            # Get final_total from the property after saving
            total = cart.final_total
            
            # Return updated cart data
            cart_data = {
                'subtotal': float(subtotal),
                'discount': float(discount),
                'vat': float(vat_amount),
                'total': float(total)
            }
            
            return JsonResponse({
                'success': True,
                'message': 'Coupon applied successfully',
                'cart_data': cart_data
            })
            
        except Exception as e:
            logger.error(f"Error applying coupon: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def remove_coupon(request):
    """Remove the applied coupon from the user's cart"""
    if request.method == 'POST':
        try:
            # Get the cart
            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'No active cart found'})
            
            # Remove coupon discount
            cart.applied_discount = Decimal('0.00')
            cart.applied_coupon = None
            
            # Recalculate VAT amount
            subtotal = cart.total_price
            vat_amount = subtotal * Decimal('0.05')  # 5% VAT
            cart.stored_vat_amount = vat_amount
            
            # Save the cart
            cart.save()
            
            # Get calculated values after saving
            total = cart.final_total
            discount = cart.applied_discount  # Should be 0.00
            
            # Return updated cart data
            cart_data = {
                'subtotal': float(subtotal),
                'discount': float(discount),
                'vat': float(vat_amount),
                'total': float(total)
            }
            
            return JsonResponse({
                'success': True,
                'message': 'Coupon removed successfully',
                'cart_data': cart_data
            })
            
        except Exception as e:
            logger.error(f"Error removing coupon: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def order_confirmation(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        expected_delivery = order.order_date + timedelta(days=7)
        
        # Format order ID
        order.formatted_id = f"PF-{order.order_date.strftime('%Y%m%d')}-{str(order.id)[-4:]}"
        
        # Parse the delivery address from JSON
        try:
            delivery_address_dict = json.loads(order.delivery_address)
            formatted_address = f"{delivery_address_dict.get('full_name')}, {delivery_address_dict.get('address_line1')}, "
            if delivery_address_dict.get('address_line2'):
                formatted_address += f"{delivery_address_dict.get('address_line2')}, "
            formatted_address += f"{delivery_address_dict.get('city')}, {delivery_address_dict.get('state')} {delivery_address_dict.get('postal_code')}"
            if delivery_address_dict.get('phone_number'):
                formatted_address += f", Phone: {delivery_address_dict.get('phone_number')}"
        except (json.JSONDecodeError, AttributeError, TypeError):
            formatted_address = order.delivery_address or "No address information available"
        
        context = {
            'order': order,
            'order_id': f"PF-{order.order_date.strftime('%Y%m%d')}-{str(order.id)[-4:]}",
            'order_date': order.order_date.strftime("%B %d, %Y"),
            'expected_delivery': expected_delivery.strftime("%B %d, %Y"),
            'grand_total': order.grand_total,  # Using the stored grand_total instead of total_amount
            'payment_method': order.payment_method,
            'delivery_address': formatted_address,  # Using the formatted address
            'cart_items': order.items.all(),
            'current_brand': None,
            'shipping_status': order.order_status,
            'payment_status': order.payment_status
        }
                
        return render(request, 'confirmation.html', context)
    except Exception as e:
        logger.error(f"Error loading order {order_id}: {str(e)}")
        return render(request, 'confirmation.html', {
            'error_message': "Couldn't load order details",
            'current_brand': None
        })

@require_POST
@login_required
def update_payment_status(request):
    data = json.loads(request.body)
    order_id = data.get('order_id')
    status = data.get('status')
    reason = data.get('reason', 'Payment process interrupted')
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        # Update the order status
        if status == 'failed' or status == 'cancelled':
            order.payment_status = 'failed'  # Or use your specific status name
            order.payment_note = reason
            order.save()
            
            # Add any other necessary actions (like email notification, etc.)
            
        return JsonResponse({'success': True})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ###########################################################################################################
@login_required(login_url='login')
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related(
        'product', 'product__brand', 'product__gender', 'product__fragrance', 'product__concentration'
    ).prefetch_related('product__varience', 'product__varience__size', 'product__images')
    
    # Process products to get the same format as in myshop
    products = []
    for item in wishlist_items:
        product = item.product
        product_data = {
            'product': product,
            'min_price': product.varience.aggregate(Min('price'))['price__min'],
            'in_stock': product.total_stock > 0,
            # Add other necessary fields
        }
        products.append(product_data)
    
    paginator = Paginator(products, 4) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wishlist_items': page_obj, 
        'page_obj': page_obj,
    }
    return render(request, 'wishlist.html', context)

@login_required(login_url='login')
def add_to_wishlist(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        try:
            product = ProductTable.objects.get(product_id=product_id)
            # Check if product already in wishlist
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=request.user,
                product=product
            )
            
            if created:
                return JsonResponse({
                    'success': True,
                    'message': 'Product added to wishlist successfully!'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': 'Product is already in your wishlist!'
                })
                
        except ProductTable.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found!'
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method!'
    }, status=400)

@login_required(login_url='login')
def remove_from_wishlist(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        try:
            wishlist_item = Wishlist.objects.get(
                user=request.user,
                product_id=product_id
            )
            wishlist_item.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Product removed from wishlist successfully!'
            })
                
        except Wishlist.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found in wishlist!'
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method!'
    }, status=400)

@login_required(login_url='login')
def get_product_variances(request, product_id):
    try:
        product = ProductTable.objects.get(product_id=product_id)
        variances = product.varience.filter(stock__gt=0).select_related('size').order_by('size__size')
        
        variances_data = [
            {
                'id': variance.id,
                'size': variance.size.size,
                'price': float(variance.price),
                'stock': variance.stock
            }
            for variance in variances
        ]
        
        return JsonResponse({
            'success': True,
            'product_name': product.product_name,
            'variances': variances_data
        })
        
    except ProductTable.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found!'
        }, status=404)

def order_list(request):
    return render(request,'order_list.html')


def contact(request):
    return render(request,'contact.html')

def loadtest(request):
    return render(request,'test.html')

import traceback
import json
import logging
from django.views import View
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Import your models


logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class PerfumeChatbotView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None
        self._initialize_openai()

    def _initialize_openai(self):
        """Initialize OpenAI client safely"""
        try:
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI API key not found - using fallback mode")
        except ImportError:
            logger.warning("OpenAI library not installed - using fallback mode")
        except Exception as e:
            logger.error(f"OpenAI initialization failed: {str(e)}")

    def post(self, request):
        """Main chatbot endpoint"""
        try:
            # Parse request data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'response': "Invalid request format. Please send valid JSON."
                }, status=400)

            user_input = data.get('message', '').strip()
            product_id = data.get('product_id')

            # Handle empty input
            if not user_input:
                return JsonResponse({
                    'status': 'success',
                    'response': "How can I help you with perfumes today?",
                    'follow_ups': [
                        "What type of fragrance do you prefer?", 
                        "Are you shopping for a special occasion?",
                        "Show me popular perfumes"
                    ]
                })

            # Generate response
            response = self._generate_response(user_input, product_id)
            follow_ups = self._get_follow_ups(user_input)

            return JsonResponse({
                'status': 'success',
                'response': response,
                'follow_ups': follow_ups
            })

        except Exception as e:
            logger.error(f"Chatbot view error: {str(e)}")
            logger.error(traceback.format_exc())
            
            return JsonResponse({
                'status': 'success',
                'response': "I'm here to help you find the perfect fragrance! What are you looking for today?",
                'follow_ups': ["Browse all products", "Popular perfumes", "Get recommendations"]
            })

    def _generate_response(self, user_input, product_id=None):
        """Generate chatbot response with fallback"""
        try:
            # Try AI response first if available
            if self.client:
                try:
                    return self._generate_ai_response(user_input, product_id)
                except Exception as e:
                    logger.warning(f"AI response failed, using fallback: {str(e)}")
            
            # Fallback to rule-based response
            return self._generate_rule_based_response(user_input, product_id)
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return "I'd love to help you find the perfect fragrance! What type of scent are you looking for?"

    def _generate_ai_response(self, user_input, product_id=None):
        """Generate AI-powered response using OpenAI"""
        messages = [{
            "role": "system",
            "content": (
                "You are ScentBot, a knowledgeable perfume expert assistant. "
                "Be helpful, friendly, and concise. Provide specific advice about fragrances. "
                "Keep responses under 200 words and suggest products when appropriate."
            )
        }]

        # Add product context if viewing specific product
        if product_id:
            try:
                product = ProductTable.objects.get(product_id=product_id)
                messages.append({
                    "role": "system",
                    "content": f"User is currently viewing: {product.product_name} by {product.brand.brand_name} - {product.fragrance.fragrance_type} fragrance for {product.occasion.occasion}"
                })
            except ProductTable.DoesNotExist:
                pass

        messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=250
        )

        return response.choices[0].message.content

    def _generate_rule_based_response(self, user_input, product_id=None):
        """Generate response using rules and database queries"""
        user_lower = user_input.lower()

        # Handle product-specific queries
        if product_id:
            try:
                product = ProductTable.objects.get(product_id=product_id)
                return (f"You're looking at **{product.product_name}** by {product.brand.brand_name}. "
                       f"This is a {product.fragrance.fragrance_type} fragrance perfect for {product.occasion.occasion}. "
                       f"Would you like to know more about this product or see similar options?")
            except ProductTable.DoesNotExist:
                pass

        # Handle different query types
        if any(word in user_lower for word in ['recommend', 'suggest', 'help me find']):
            return self._get_recommendations(user_input)
        
        elif any(word in user_lower for word in ['price', 'cost', 'expensive', 'budget']):
            return ("Our perfumes range from affordable to luxury options. "
                   "What's your budget range, and what type of fragrance interests you?")
        
        elif any(word in user_lower for word in ['popular', 'best', 'trending']):
            return self._get_popular_products()
        
        elif any(word in user_lower for word in ['floral', 'flower']):
            return ("Floral fragrances are perfect for a feminine, romantic touch! "
                   "They feature notes like rose, jasmine, or lily. Would you like to see our floral collection?")
        
        elif any(word in user_lower for word in ['woody', 'wood']):
            return ("Woody fragrances offer sophistication with notes like cedar, sandalwood, or oud. "
                   "Perfect for those who prefer deeper, more grounded scents.")
        
        elif any(word in user_lower for word in ['fresh', 'citrus']):
            return ("Fresh and citrus fragrances are energizing and perfect for daily wear! "
                   "Think lemon, bergamot, or ocean breeze scents.")
        
        else:
            return ("I'd be happy to help you find the perfect fragrance! "
                   "Are you looking for something floral, woody, fresh, or perhaps for a specific occasion?")

    def _get_recommendations(self, user_input):
        """Get product recommendations based on user input"""
        try:
            # Extract preferences from user input
            filters = self._extract_preferences(user_input)
            
            # Build query
            query = Q(is_active=True)
            if filters['gender']:
                query &= Q(gender=filters['gender'])
            if filters['fragrance']:
                query &= Q(fragrance=filters['fragrance'])
            if filters['brand']:
                query &= Q(brand=filters['brand'])
            if filters['occasion']:
                query &= Q(occasion=filters['occasion'])

            products = ProductTable.objects.filter(query)[:3]

            if products:
                response = "Here are some great options for you:\n\n"
                for i, product in enumerate(products, 1):
                    response += f"{i}. **{product.product_name}** by {product.brand.brand_name}\n"
                    response += f"   - {product.fragrance.fragrance_type} fragrance\n"
                    response += f"   - Perfect for {product.occasion.occasion}\n\n"
                return response
            else:
                return ("I'd love to help you find something perfect! Could you tell me more? "
                       "For example, do you prefer floral or woody scents? Daily wear or special occasions?")

        except Exception as e:
            logger.error(f"Recommendations failed: {str(e)}")
            return "I can help you find great fragrances! What type of scent do you prefer?"

    def _get_popular_products(self):
        """Get popular products response"""
        try:
            products = ProductTable.objects.filter(is_active=True)[:3]
            
            if products:
                response = "Here are some of our popular fragrances:\n\n"
                for product in products:
                    response += f"• **{product.product_name}** by {product.brand.brand_name}\n"
                    response += f"  {product.fragrance.fragrance_type} - Perfect for {product.occasion.occasion}\n\n"
                return response
            else:
                return "We have many wonderful fragrances available! What type of scent interests you most?"

        except Exception as e:
            logger.error(f"Popular products query failed: {str(e)}")
            return "We have a great selection of popular fragrances! What are you in the mood for?"

    def _extract_preferences(self, user_input):
        """Extract user preferences from input"""
        preferences = {
            'gender': None,
            'fragrance': None,
            'occasion': None,
            'brand': None
        }

        try:
            user_lower = user_input.lower()

            # Extract gender
            preferences['gender'] = self._extract_gender(user_lower)
            preferences['fragrance'] = self._extract_fragrance(user_lower)
            preferences['occasion'] = self._extract_occasion(user_lower)
            preferences['brand'] = self._extract_brand(user_lower)

        except Exception as e:
            logger.error(f"Preference extraction failed: {str(e)}")

        return preferences

    def _extract_gender(self, text):
        """Extract gender from text"""
        try:
            # Check database genders first
            genders = Gender.objects.all()
            for gender in genders:
                if gender.gender.lower() in text:
                    return gender

            # Check common terms
            gender_terms = {
                'male': ['man', 'men', 'male', 'masculine', 'guy', 'boy', 'gentleman'],
                'female': ['woman', 'women', 'female', 'feminine', 'girl', 'lady'],
                'unisex': ['unisex', 'both', 'either', 'everyone']
            }

            for gender_name, terms in gender_terms.items():
                if any(term in text for term in terms):
                    return Gender.objects.filter(gender__icontains=gender_name).first()

        except Exception as e:
            logger.error(f"Gender extraction failed: {str(e)}")
        
        return None

    def _extract_fragrance(self, text):
        """Extract fragrance type from text"""
        try:
            # Check database fragrances first
            fragrances = Fragrance.objects.all()
            for fragrance in fragrances:
                if fragrance.fragrance_type.lower() in text:
                    return fragrance

            # Check fragrance families
            fragrance_families = {
                'citrus': ['citrus', 'lemon', 'lime', 'orange', 'fresh'],
                'floral': ['floral', 'flower', 'rose', 'jasmine', 'feminine'],
                'woody': ['woody', 'wood', 'cedar', 'sandalwood', 'earthy'],
                'oriental': ['oriental', 'spicy', 'vanilla', 'warm', 'sensual'],
                'fruity': ['fruity', 'fruit', 'apple', 'berry', 'sweet']
            }

            for family_name, keywords in fragrance_families.items():
                if any(keyword in text for keyword in keywords):
                    return fragrances.filter(fragrance_type__icontains=family_name).first()

        except Exception as e:
            logger.error(f"Fragrance extraction failed: {str(e)}")
        
        return None

    def _extract_occasion(self, text):
        """Extract occasion from text"""
        try:
            # Check database occasions first
            occasions = Occasion.objects.all()
            for occasion in occasions:
                if occasion.occasion.lower() in text:
                    return occasion

            # Check common terms
            occasion_terms = {
                'casual': ['daily', 'everyday', 'casual', 'regular'],
                'formal': ['formal', 'special', 'elegant', 'evening'],
                'office': ['work', 'office', 'business', 'professional'],
                'romantic': ['date', 'romantic', 'dinner', 'anniversary']
            }

            for occasion_name, terms in occasion_terms.items():
                if any(term in text for term in terms):
                    return occasions.filter(occasion__icontains=occasion_name).first()

        except Exception as e:
            logger.error(f"Occasion extraction failed: {str(e)}")
        
        return None

    def _extract_brand(self, text):
        """Extract brand from text"""
        try:
            brands = BrandTable.objects.all()
            
            # Check exact matches first
            for brand in brands:
                if brand.brand_name.lower() in text:
                    return brand

            # Check partial matches
            words = text.split()
            for word in words:
                if len(word) > 3:
                    brand_match = brands.filter(brand_name__icontains=word).first()
                    if brand_match:
                        return brand_match

        except Exception as e:
            logger.error(f"Brand extraction failed: {str(e)}")
        
        return None

    def _get_follow_ups(self, user_input):
        """Generate follow-up questions based on user input"""
        try:
            user_lower = user_input.lower()

            if any(word in user_lower for word in ['recommend', 'suggest']):
                return [
                    "Tell me more about these options",
                    "What's the price range?",
                    "Show me similar products"
                ]
            elif any(word in user_lower for word in ['price', 'cost']):
                return [
                    "Show me budget-friendly options",
                    "What sizes are available?",
                    "Any current promotions?"
                ]
            elif any(word in user_lower for word in ['popular', 'best']):
                return [
                    "What makes these special?",
                    "Show me customer reviews",
                    "Any new arrivals?"
                ]
            else:
                return [
                    "What occasions are you shopping for?",
                    "Do you prefer light or strong fragrances?",
                    "What's your budget range?"
                ]

        except Exception as e:
            logger.error(f"Follow-ups generation failed: {str(e)}")
            return [
                "Browse our collection",
                "Get personalized recommendations",
                "Contact our experts"
            ]