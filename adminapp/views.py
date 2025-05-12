from .models import  Gender, Occasion, SizeTable, Fragrance, BrandTable, ConcentrationType,ProductTable,ProductImage,VarienceTable,Wallet,WalletTransaction,OfferTable,coupon
from authentication1.models import usertable
from user.models import  Order, OrderItem
from django.contrib.auth.models import User 
from django.db.models import Q
from django.urls import reverse
from decimal import Decimal
import logging
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import TruncDate

from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.utils import timezone
import os
from django.conf import settings
from datetime import datetime
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from datetime import datetime, timedelta
import calendar
from django.http import HttpResponseRedirect
from decimal import Decimal
import json
import logging
logger = logging.getLogger(__name__)
from functools import wraps

# Create your views here.
def mainauthenticate(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('adminlog')
        return view_func(request, *args, **kwargs)
    return wrapper

@never_cache
@csrf_protect
def adminlog(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect("adminhome")

    if request.method == "POST":
        adminemail = request.POST.get("ademail", "").strip()
        adminpassword = request.POST.get("adpass", "").strip()

        # Validate input
        if not adminemail or not adminpassword:
            messages.error(request, "Please enter both email and password.")
            return render(request, "adminlog.html")

        # Use the custom EmailBackend for authentication
        admin_user = authenticate(request, email=adminemail, password=adminpassword)
        
        if admin_user is not None and admin_user.is_superuser:
            login(request, admin_user)
            messages.success(request, "Admin login successful.")
            return redirect("adminhome")
        else:
            messages.error(request, "Invalid admin credentials or insufficient privileges.")

    return render(request, 'adminlog.html')
# #################################################################################################################################################
@mainauthenticate
@login_required(login_url='adminlog')
def adminhome(request):
    """
    Renders the admin home page with the dashboard
    """
    
    recent_orders = Order.objects.filter(
        order_date__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    
    overall_revenue = Order.objects.filter(
        payment_status='PAID'
    ).aggregate(
        revenue=Sum('total_amount', default=0)
    )['revenue'] or 0
    
    
    best_selling_products = get_best_selling_products()
    
    
    best_selling_categories = get_best_selling_categories()
    
    context = {
        'recent_orders': recent_orders,
        'overall_revenue': overall_revenue,
        'best_selling_products': best_selling_products,
        'best_selling_categories': best_selling_categories
    }
    
    return render(request, 'adminHome.html', context)

@login_required(login_url='adminlog')
def sales_report(request):
    try:
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                filter_type = data.get('filter', 'Daily')
                start_date = data.get('startDate')
                end_date = data.get('endDate')
                specific_date = data.get('specificDate')
                
                if start_date:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                if end_date:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                
                orders = get_filtered_orders(filter_type, start_date, end_date, specific_date)
                table_data = prepare_table_data(orders, filter_type)
                summary_data = calculate_summary_data(orders)
                
                return JsonResponse({
                    'success': True,
                    'data': table_data,
                    'summary': summary_data
                })
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
            except ValueError as e:
                return JsonResponse({'success': False, 'message': f'Invalid date format: {str(e)}'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error processing request: {str(e)}'}, status=500)
        
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Unexpected error: {str(e)}'}, status=500)


def get_filtered_orders(filter_type, start_date=None, end_date=None, specific_date=None):
    try:
        now = timezone.now()
        orders = Order.objects.all()
        
        if filter_type == 'Daily':
            if specific_date:
                # Use the specific date passed from the frontend
                specific_date = datetime.strptime(specific_date, '%Y-%m-%d')
                start_of_day = specific_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = specific_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                orders = orders.filter(order_date__range=(start_of_day, end_of_day))
            else:
                # Default to today if no specific date is provided
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                orders = orders.filter(order_date__range=(today, end_of_today))
        elif filter_type == 'Weekly':
            start_date = now - timedelta(weeks=4)
            orders = orders.filter(order_date__gte=start_date)
        elif filter_type == 'Monthly':
            start_date = now - timedelta(days=180)
            orders = orders.filter(order_date__gte=start_date)
        elif filter_type == 'Yearly':
            start_date = now - timedelta(days=365)
            orders = orders.filter(order_date__gte=start_date)
        elif filter_type == 'Custom Date Range' and start_date and end_date:
            orders = orders.filter(order_date__range=(start_date, end_date))
        
        return orders
    except Exception as e:
        raise Exception(f"Error filtering orders: {str(e)}")

@login_required(login_url='adminlog')
def detailed_orders(request):
    try:
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                date_str = data.get('date')
                
                if not date_str:
                    return JsonResponse({'success': False, 'message': 'Date is required'}, status=400)
                
                # Parse the date string (could be YYYY-MM-DD, Month YYYY, etc.)
                try:
                    # Try to parse as YYYY-MM-DD
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    start_date = date_obj.replace(hour=0, minute=0, second=0)
                    end_date = date_obj.replace(hour=23, minute=59, second=59)
                except ValueError:
                    try:
                        # Try to parse as Month YYYY
                        date_obj = datetime.strptime(date_str, '%B %Y')
                        start_date = date_obj.replace(day=1, hour=0, minute=0, second=0)
                        next_month = date_obj.replace(day=28) + timedelta(days=4)
                        end_date = next_month - timedelta(days=next_month.day)
                        end_date = end_date.replace(hour=23, minute=59, second=59)
                    except ValueError:
                        try:
                            # Try to parse as Week W, YYYY
                            parts = date_str.split(', ')
                            if len(parts) == 2 and parts[0].startswith('Week '):
                                week_num = int(parts[0].replace('Week ', ''))
                                year = int(parts[1])
                                first_day = datetime(year, 1, 1) + timedelta(days=(week_num-1)*7)
                                start_date = first_day
                                end_date = first_day + timedelta(days=6, hours=23, minutes=59, seconds=59)
                            else:
                                raise ValueError("Unsupported date format")
                        except:
                            try:
                                # Try to parse as YYYY
                                year = int(date_str)
                                start_date = datetime(year, 1, 1)
                                end_date = datetime(year, 12, 31, 23, 59, 59)
                            except:
                                return JsonResponse({'success': False, 'message': 'Invalid date format'}, status=400)
                
                # Get orders for the specified date range
                orders = Order.objects.filter(order_date__range=(start_date, end_date))
                
                # Serialize the orders with detailed information
                orders_data = []
                for order in orders:
                    user_data = None
                    if order.user:
                        user_data = {
                            'id': order.user.id,
                            'username': order.user.username
                        }
                    
                    items_count = OrderItem.objects.filter(order=order).aggregate(
                        total=Sum('quantity')
                    )['total'] or 0
                    
                    orders_data.append({
                        'id': order.id,
                        'created_at': order.order_date.isoformat(),
                        'total_amount': float(order.total_amount),
                        'subtotal': float(order.subtotal),
                        'discount_amount': float(order.discount_amount),
                        'order_status': order.order_status,
                        'payment_status': order.payment_status,
                        'payment_method': order.payment_method,
                        'is_returned': order.is_returned,
                        'user': user_data,
                        'items_count': items_count
                    })
                
                return JsonResponse({
                    'success': True,
                    'orders': orders_data
                })
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error processing request: {str(e)}'}, status=500)
        
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Unexpected error: {str(e)}'}, status=500)
    

@login_required(login_url='adminlog')
def order_items(request):
    try:
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                order_id = data.get('orderId')
                
                if not order_id:
                    return JsonResponse({'success': False, 'message': 'Order ID is required'}, status=400)
                
                try:
                    order = Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)
                
                # Get order items
                order_items = OrderItem.objects.filter(order=order)
                
                # Serialize items
                items_data = []
                for item in order_items:
                    product_name = "Unknown Product"
                    variant = None
                    if item.product_variation and hasattr(item.product_variation, 'product'):
                        product_name = item.product_variation.product.product_name
                        variant = item.product_variation.variation_value
                    
                    items_data.append({
                        'id': item.id,
                        'product_name': product_name,
                        'variant': variant,
                        'price': float(item.price),
                        'quantity': item.quantity
                    })
                
                # Serialize order for context
                user_data = None
                if order.user:
                    user_data = {
                        'id': order.user.id,
                        'username': order.user.username
                    }
                
                order_data = {
                    'id': order.id,
                    'created_at': order.order_date.isoformat(),
                    'total_amount': float(order.total_amount),
                    'subtotal': float(order.subtotal),
                    'discount_amount': float(order.discount_amount),
                    'order_status': order.order_status,
                    'payment_status': order.payment_status,
                    'payment_method': order.payment_method,
                    'is_returned': order.is_returned,
                    'user': user_data
                }
                
                return JsonResponse({
                    'success': True,
                    'items': items_data,
                    'order': order_data
                })
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error processing request: {str(e)}'}, status=500)
        
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Unexpected error: {str(e)}'}, status=500)


def prepare_table_data(orders, filter_type):
    try:
        truncate_function = TruncDate  
        date_format = '%Y-%m-%d'
        
        if filter_type == 'Weekly':
            truncate_function = TruncWeek
            date_format = 'Week %W, %Y'
        elif filter_type == 'Monthly':
            truncate_function = TruncMonth
            date_format = '%B %Y'
        elif filter_type == 'Yearly':
            truncate_function = TruncYear
            date_format = '%Y'
        
        orders = orders.annotate(date_period=truncate_function('order_date'))
        
        sales_data = orders.values('date_period').annotate(
            totalSalesRevenue=Sum('total_amount', default=0),
            numberOfOrders=Count('id'),
        ).order_by('date_period')
        
        result = []
        for data in sales_data:
            try:
                date_period = data['date_period']
                
                if isinstance(date_period, datetime):
                    formatted_date = date_period.strftime(date_format)
                else:
                    formatted_date = str(date_period)
                
                period_orders = orders.filter(date_period=date_period)
                order_ids = period_orders.values_list('id', flat=True)
                
                total_items = OrderItem.objects.filter(order_id__in=order_ids).aggregate(
                    total=Sum('quantity', default=0)
                )['total'] or 0
                
                total_items_value = OrderItem.objects.filter(order_id__in=order_ids).aggregate(
                    total=Sum(F('price') * F('quantity'), default=0)
                )['total'] or 0
                
                total_sales_revenue = data['totalSalesRevenue'] or 0
                discount_applied = max(0, total_items_value - total_sales_revenue)
                
                result.append({
                    'date': formatted_date,
                    'totalSalesRevenue': float(total_sales_revenue),
                    'discountApplied': float(discount_applied),
                    'netSales': float(total_sales_revenue - discount_applied),
                    'numberOfOrders': data['numberOfOrders'],
                    'totalItemsSold': total_items,
                    'orders': []  # Will be populated in detailed_orders view
                })
            except Exception as e:
                continue  # Skip this record if there's an error
        
        return result
    except Exception as e:
        raise Exception(f"Error preparing table data: {str(e)}")
    
def calculate_summary_data(orders):
    try:
        total_sales_count = orders.count()
        overall_order_amount = orders.aggregate(
            total=Sum('total_amount', default=0)
        )['total'] or 0
        
        order_ids = orders.values_list('id', flat=True)
        total_items_value = OrderItem.objects.filter(order_id__in=order_ids).aggregate(
            total=Sum(F('price') * F('quantity'), default=0)
        )['total'] or 0
        
        overall_discount = max(0, total_items_value - overall_order_amount)
        
        return {
            'totalSalesCount': total_sales_count,
            'overallOrderAmount': float(overall_order_amount),
            'overallDiscount': float(overall_discount)
        }
    except Exception as e:
        raise Exception(f"Error calculating summary data: {str(e)}")
    

def get_best_selling_categories(limit=3):
    try:
        best_categories = OrderItem.objects.values(
            'product_variation__product__brand__brand_id',
            'product_variation__product__brand__brand_name'
        ).annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')[:limit]
        
        result = []
        for i, category in enumerate(best_categories, 1):
            try:
                result.append({
                    'rank': i,
                    'name': category['product_variation__product__brand__brand_name'],
                    'total_sold': category['total_sold']
                })
            except Exception as e:
                continue  # Skip this category if there's an error
        
        return result
    except Exception as e:
        raise Exception(f"Error getting best selling categories: {str(e)}")

def get_best_selling_products(limit=10):
    try:
        best_products = OrderItem.objects.values(
            'product_variation__product__product_id',
            'product_variation__product__product_name'
        ).annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')[:limit]
        
        result = []
        for i, product in enumerate(best_products, 1):
            try:
                product_id = product['product_variation__product__product_id']
                try:
                    product_obj = ProductTable.objects.get(product_id=product_id)
                    image = product_obj.images.first()
                    image_url = image.image.url if image else None
                except ProductTable.DoesNotExist:
                    image_url = None
                    
                result.append({
                    'rank': i,
                    'name': product['product_variation__product__product_name'],
                    'total_sold': product['total_sold'],
                    'image_url': image_url
                })
            except Exception as e:
                continue  # Skip this product if there's an error
        
        return result
    except Exception as e:
        raise Exception(f"Error getting best selling products: {str(e)}")

@mainauthenticate
@login_required(login_url='adminlog')
def sales_chart_data(request):
    try:
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                filter_type = data.get('filter', 'Monthly')
                start_date = data.get('startDate')
                end_date = data.get('endDate')
                
                if start_date:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                if end_date:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                
                orders = get_filtered_orders(filter_type, start_date, end_date)
                chart_data = prepare_chart_data(orders, filter_type)
                
                return JsonResponse({
                    'success': True,
                    'data': chart_data
                })
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
            except ValueError as e:
                return JsonResponse({'success': False, 'message': f'Invalid date format: {str(e)}'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error processing request: {str(e)}'}, status=500)
        
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Unexpected error: {str(e)}'}, status=500)

def prepare_chart_data(orders, filter_type):
    try:
        truncate_function = TruncDate  
        date_format = '%Y-%m-%d'
        
        if filter_type == 'Weekly':
            truncate_function = TruncWeek
            date_format = 'Week %W, %Y'
        elif filter_type == 'Monthly':
            truncate_function = TruncMonth
            date_format = '%B %Y'
        elif filter_type == 'Yearly':
            truncate_function = TruncYear
            date_format = '%Y'
        
        orders = orders.annotate(date_period=truncate_function('order_date'))
        
        sales_data = orders.values('date_period').annotate(
            revenue=Sum('total_amount', default=0),
            orders_count=Count('id'),
        ).order_by('date_period')
        
        labels = []
        revenue_data = []
        orders_data = []
        
        for data in sales_data:
            try:
                date_period = data['date_period']
                
                if isinstance(date_period, datetime):
                    formatted_date = date_period.strftime(date_format)
                else:
                    formatted_date = str(date_period)
                
                labels.append(formatted_date)
                revenue_data.append(float(data['revenue'] or 0))
                orders_data.append(data['orders_count'])
            except Exception as e:
                continue  # Skip this record if there's an error
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Revenue',
                    'data': revenue_data,
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 1,
                    'yAxisID': 'y'
                },
                {
                    'label': 'Orders',
                    'data': orders_data,
                    'backgroundColor': 'rgba(153, 102, 255, 0.2)',
                    'borderColor': 'rgba(153, 102, 255, 1)',
                    'borderWidth': 1,
                    'yAxisID': 'y1'
                }
            ]
        }
    except Exception as e:
        raise Exception(f"Error preparing chart data: {str(e)}")



@login_required(login_url='adminlog')
def best_selling_products(request):
    try:
        products = get_best_selling_products()
        return JsonResponse({
            'success': True,
            'products': products
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error getting best selling products: {str(e)}'
        }, status=500)

@login_required(login_url='adminlog')
def best_selling_categories(request):
    try:
        categories = get_best_selling_categories()
        return JsonResponse({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error getting best selling categories: {str(e)}'
        }, status=500)
# ##################################################################################################################################################
@mainauthenticate
@login_required(login_url='adminlog')
def admincategory(request):
    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')
        
        # Improved validation
        if not brand_name or not brand_name.strip():
            messages.error(request, "Brand name cannot be empty.")
            return HttpResponseRedirect(f"{reverse('adcategory')}?action=add&error={messages.error}")
            
        # Check if the brand already exists (case-insensitive)
        existing_brand = BrandTable.objects.filter(brand_name__iexact=brand_name.strip()).exists()
        if existing_brand:
            error_msg = f"Brand '{brand_name}' already exists."
            messages.error(request, error_msg)
            return HttpResponseRedirect(f"{reverse('adcategory')}?action=add&error={error_msg}")
            
        # Create the brand if validation passes
        BrandTable.objects.create(brand_name=brand_name.strip())
        messages.success(request, f"Brand '{brand_name}' added successfully!")
        return redirect('adcategory')

    # Get all brands for display
    brands = BrandTable.objects.all().order_by('-brand_id')

    # Set up pagination
    paginator = Paginator(brands, 10)  
    page = request.GET.get('page', 1)

    try:
        paginated_brands = paginator.page(page)
    except:
        paginated_brands = paginator.page(1)

    context = {
        'brands': paginated_brands,
        'currentPage': int(page),
        'totalPages': paginator.num_pages,
    }

    return render(request, 'categoryManagement.html', context)



@login_required(login_url='adminlog')
def edit_category(request, brand_id):
    brand = get_object_or_404(BrandTable, brand_id=brand_id)

    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')
        
        # Improved validation
        if not brand_name or not brand_name.strip():
            error_msg = "Brand name cannot be empty."
            messages.error(request, error_msg)
            return HttpResponseRedirect(f"{reverse('adcategory')}?action=edit&brand_id={brand_id}&error={error_msg}")
        
        # Check if another brand with the same name exists
        existing_brand = BrandTable.objects.filter(brand_name__iexact=brand_name.strip()).exclude(brand_id=brand_id).exists()
        if existing_brand:
            error_msg = f"Brand '{brand_name}' already exists."
            messages.error(request, error_msg)
            return HttpResponseRedirect(f"{reverse('adcategory')}?action=edit&brand_id={brand_id}&error={error_msg}")
            
        # Update the brand if validation passes
        brand.brand_name = brand_name.strip()
        brand.save()
        messages.success(request, f"Brand '{brand_name}' updated successfully!")

    return redirect('adcategory')


@login_required(login_url='adminlog')
def toggle_category_status(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(ProductTable, product_id=product_id)
        product.is_active = not product.is_active
        product.save()
        
        status_message = "listed" if product.is_active else "unlisted"
        messages.success(request, f"Product {product.product_name} has been {status_message} successfully.")
    
    return redirect('adproducts')

# ####################################################################################################################

def toggle_product_status(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(ProductTable, product_id=product_id)
        product.is_active = not product.is_active
        product.save()
        
        status_message = "listed" if product.is_active else "unlisted"
        messages.success(request, f"Product {product.product_name} has been {status_message} successfully.")
    
    return redirect('adproducts')
# ####################################### ADD PRODUCTS SECTION###########################################################

@login_required(login_url='adminlog')
def adproductpage(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('adminlog')


    all_products = ProductTable.objects.all().order_by('-product_id').prefetch_related('images', 'varience').select_related(
    'gender', 'fragrance', 'concentration', 'occasion', 'brand'
)
    
    
    paginator = Paginator(all_products, 10)
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)
    
    # Get all lookup data needed for the form
    genders = Gender.objects.all()
    sizes = SizeTable.objects.all()
    fragrances = Fragrance.objects.all()
    concentrations = ConcentrationType.objects.all()
    occasions = Occasion.objects.all()
    brands = BrandTable.objects.all()
    
    # Check if there's a POST request (adding a new product)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        gender_id = request.POST.get('gender')
        fragrance_id = request.POST.get('fragrance')
        concentration_id = request.POST.get('concentration')
        occasion_id = request.POST.get('occasion')
        brand_id = request.POST.get('brand')
        
        
        product = ProductTable.objects.create(
            product_name=name,
            description=description,
            gender_id=gender_id,
            fragrance_id=fragrance_id,
            concentration_id=concentration_id,
            occasion_id=occasion_id,
            brand_id=brand_id
        )
        
        # Handle image uploads
        image_fields = ['product_image_1', 'product_image_2', 'product_image_3']
        for field in image_fields:
            if field in request.FILES:
                ProductImage.objects.create(
                    product=product,
                    image=request.FILES[field]
                )
        
        # Redirect to variance page to add initial variance
        return redirect('product_variance', product_id=product.product_id)
    
    # Annotate products with total stock from variances
    # for product in products:
    #     product.total_stock = product.total_stock
    #     product.isOutOfStock = product.total_stock <= 0
    
    context = {
        'products': products,
        'genders': genders,
        'sizes': sizes,
        'fragrances': fragrances,
        'concentrations': concentrations,
        'occasions': occasions,
        'brands': brands,
    }
    
    return render(request, 'productManagement.html', context)


# ########################################################################################################

@login_required(login_url='adminlog')
def viewproduct(request, product_id=None):
    products = ProductTable.objects.prefetch_related('images').all()
    
    context = {
        'products': products,
        'genders': Gender.objects.all(),
        'fragrances': Fragrance.objects.all(),
        'concentrations': ConcentrationType.objects.all(),
        'occasions': Occasion.objects.all(),
        'brands': BrandTable.objects.all(),
    }
    
    return render(request, 'productManagement.html', context) 
# ###################################################################################################################

@login_required(login_url='adminlog')
def product_variance(request, product_id):
    product = get_object_or_404(ProductTable, product_id=product_id)
    sizes = SizeTable.objects.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            size_id = request.POST.get('size')
            stock = request.POST.get('stock')
            price = request.POST.get('price')
            
            # Validate inputs
            if not all([size_id, stock, price]):
                messages.error(request, 'All fields are required')
                return redirect('product_variance', product_id=product_id)
            
            # Get size object
            size = get_object_or_404(SizeTable, size_id=size_id)
            
            # Check if variance already exists
            existing_variance = VarienceTable.objects.filter(
                product=product, 
                size=size
            ).first()
            
            if existing_variance:
                # Update existing variance
                existing_variance.stock = stock
                existing_variance.price = price
                existing_variance.save()
                messages.success(request, 'Variance updated successfully')
            else:
                # Create new variance
                VarienceTable.objects.create(
                    product=product,
                    size=size,
                    stock=stock,
                    price=price
                )
                messages.success(request, 'Variance added successfully')
            
            return redirect('product_variance', product_id=product_id)
        
        except Exception as e:
            messages.error(request, f'Error adding variance: {str(e)}')
            return redirect('product_variance', product_id=product_id)
    
    # GET request
    variances = VarienceTable.objects.filter(product=product)
    
    context = {
        'product': product,
        'sizes': sizes,
        'variances': variances
    }
    
    return render(request, 'product_variance.html', context)

# ####################################################### EDIT PRODUCT SECTION#########################################
@login_required(login_url='adminlog')
def editproducts(request, product_id=None):
    
    if product_id:
        product = get_object_or_404(ProductTable, product_id=product_id)
        
        if request.method == 'POST':
            try:
                # Update product details
                product.product_name = request.POST.get('name')
                product.description = request.POST.get('description')
                product.gender_id = request.POST.get('gender')
                product.size_id = request.POST.get('size')
                product.fragrance_id = request.POST.get('fragrance')
                product.concentration_id = request.POST.get('concentration')
                product.occasion_id = request.POST.get('occasion')
                product.brand_id = request.POST.get('brand')
                product.price = request.POST.get('price')
                product.stock = request.POST.get('stock')
                product.save()
                
                # Handle image uploads
                images = product.images.all()
                
                # Get all uploaded images
                uploaded_images = [
                    request.FILES.get('product_image_1'),
                    request.FILES.get('product_image_2'),
                    request.FILES.get('product_image_3')
                ]
                
                # Delete existing images if new ones are uploaded
                if any(uploaded_images):
                    product.images.all().delete()
                    
                    # Create new images
                    for image in uploaded_images:
                        if image:
                            ProductImage.objects.create(
                                product=product,
                                image=image
                            )
                
                messages.success(request, "Product updated successfully!")
                return redirect('adproducts')
            except Exception as e:
                messages.error(request, f"Error updating product: {str(e)}")
                return redirect('editproduct', product_id=product_id)
    
    # If no product_id, show product listing
    products_list = ProductTable.objects.all().order_by('-product_id')
    paginator = Paginator(products_list, 5)
    page = request.GET.get('page', 1)
    
    try:
        products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)
    
    context = {
        'products': products,
        'genders': Gender.objects.all(),
        'sizes': SizeTable.objects.all(),
        'fragrances': Fragrance.objects.all(),
        'concentrations': ConcentrationType.objects.all(),
        'occasions': Occasion.objects.all(),
        'brands': BrandTable.objects.all(),
        'totalPages': paginator.num_pages,
        'currentPage': int(page),
    }
    
    return render(request, 'productManagement.html', context)

# ################################################################################################################

@login_required(login_url='adminlog')
def adusermanage(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('adminlog')
    
    users_list = usertable.objects.all().order_by('-id')
    search_query = request.GET.get('search', '')
    
    if search_query:
        filtered_users = users_list.filter(
            Q(firstname__icontains=search_query) |
            Q(lastname__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phonenumber__icontains=search_query)
        )
        if not filtered_users:
            messages.warning(request, f"No users found matching '{search_query}'")
            users_list = usertable.objects.all().order_by('firstname')
        else:
            users_list = filtered_users

    paginator = Paginator(users_list, 5)
    page_number = request.GET.get('page')
    
    try:
        users = paginator.page(page_number)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)


    context = {
        "users": users,
        "search_query": search_query,
    }

    response = render(request, 'userManagement.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def toggle_user_status(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('adminlog')
        
    if request.method == 'POST':
        user = get_object_or_404(usertable, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status_message = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.firstname} {user.lastname} has been {status_message} successfully.")
    
    return redirect('adminuser')
# #############################################################################

def toggle_user_status(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(usertable, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status_message = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.firstname} {user.lastname} has been {status_message} successfully.")
    
    return redirect('adminuser')
# ############################################################################################################################
@login_required(login_url='adminlog')
def ordermanagement(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('adminlog')
    

    search_query = request.GET.get('search', '')
    orders = Order.objects.all().order_by('-order_date')
    
    if search_query:
        orders = orders.filter(
            Q(user__firstname__icontains=search_query) | 
            Q(user__lastname__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__phonenumber__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    
    paginator = Paginator(orders, 5) 
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'currentPage': int(page_number),
        'totalPages': paginator.num_pages,
        'search_query': search_query,
    }
    return render(request, 'orderManagement.html', context)


@login_required(login_url='adminlog')
def vieworder(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id)

    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'viewOrder.html', context)


def update_order_status(request):
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id')
            new_status = request.POST.get('status')
            
            order = get_object_or_404(Order, id=order_id)
            old_status = order.order_status
            
            # Update order status
            order.order_status = new_status
            
            # Handle cancellation
            if new_status == 'Cancelled':
                order.is_cancelled = True
                order.canceled_date = timezone.now()
                
                # Return items to inventory
                order_items = order.items.all()
                for item in order_items:
                    if not item.is_cancelled:
                        product_variation = item.product_variation
                        if product_variation:
                            product_variation.stock += item.quantity
                            product_variation.save()
                        
                        item.is_cancelled = True
                        item.save()
                
                
                if order.payment_status == 'PAID' and not order.is_returned and order.payment_method != 'Cash on Delivery':
                    user = order.user
                    refund_amount = order.total_amount
                    
                    # Use the exact pattern from the working function
                    try:
                        wallet, created = Wallet.objects.get_or_create(
                            user=user,
                            defaults={'balance': Decimal('0.00')}  # Start with zero balance if new wallet
                        )
                        
                        # Add refund to wallet
                        wallet.balance += Decimal(refund_amount)
                        wallet.save()
                        
                        # Create wallet transaction record
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_amount=refund_amount,
                            transaction_type='refund',
                            description=f'Refund for admin-cancelled order #{order.id}'
                        )
                        
                        # Update order payment status
                        order.payment_status = 'Refunded'
                        order.refund_amount = refund_amount
                        order.refund_date = timezone.now()
                        
                    except Exception as e:
                        import traceback
                        print(f"ERROR PROCESSING REFUND: {str(e)}")
                        print(traceback.format_exc())
            
            # Handle delivery
            if new_status == 'Delivered':
                order.delivery_date = timezone.now()
            
            # Save changes
            order.save()
            
            return JsonResponse({'success': True, 'message': f'Order status updated from {old_status} to {new_status}'})
            
        except Exception as e:
            import traceback
            print(f"ERROR IN UPDATE_ORDER_STATUS: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

# #######################################################approve and disapprove########################################################################

@login_required(login_url='adminlog')
def approve_return_request(request):
    if not request.user.is_superuser:
        messages.error(request,"access denied admin privileges required")
        return redirect('adminlog')
    
    if request.method == 'POST':

        try:
            
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                order_id = data.get('order_id')
            else:
                order_id = request.POST.get('order_id')
                
            if not order_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Order ID is required'
                }, status=400)
                
            order = get_object_or_404(Order, id=order_id)
            
            if order.is_returned:
                return JsonResponse({
                    'success': False,
                    'message': 'Order has already been returned'
                }, status=400)
                
            if not order.return_reason:
                return JsonResponse({
                    'success': False,
                    'message': 'No return reason provided for this order'
                }, status=400)

            
            order.order_status = 'Returned'
            order.is_returned = True
            order.return_status = order.RETURN_COMPLETED
            order.return_date = timezone.now()
            order.save()
            
           
            user = order.user
            refund_amount = order.total_amount
            
            try:
                
                wallet, created = Wallet.objects.get_or_create(
                    user=user,
                    defaults={'balance': Decimal(refund_amount)}
                )
                
                if not created:
                    wallet.balance += Decimal(refund_amount)
                    wallet.save()
                
               
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_amount=refund_amount,
                    transaction_type='refund',
                    description=f'Refund for returned order #{order.id}'
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Return approved and refund processed to user wallet'
                })
                
            except Exception as e:
               
                order.order_status = 'Pending Return'
                order.is_returned = False
                order.save()
                raise e
                
        except Exception as e:
            logger.error(f"Error in approve_return_request: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)


@login_required
def reject_return_request(request):
    if not request.user.is_superuser:
        messages.error(request,"access denied admin privileges requred")
        return redirect('adminlog')
    
    if request.method=='POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                order_id = data.get('order_id')
            else:
                order_id = request.POST.get('order_id')
            if not order_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Order ID is required'
                }, status=400)
            
            order = get_object_or_404(Order, id=order_id)

            if order.is_returned:
                return JsonResponse({
                    'success': False,
                    'message': 'Order has already been returned'
                }, status=400)
            
            
            order.return_status = order.RETURN_REJECTED
           
            order.return_reason = None
            order.save()

            return JsonResponse({
                'success': True,
                'message': 'Return request rejected successfully'
            })
        except Exception as e:
            logger.error(f"Error in reject_return_request: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@login_required(login_url='adminlog')
def approve_item_return_request(request):
    if not request.user.is_superuser:
        messages.error(request,"access denied admin privileges required")
        return redirect('adminlog')

    if request.method == 'POST':
        try:
            if request.content_type  == 'application/json':
                data = json.loads(request.body)
                item_id= data.get('item_id')
            else:
                item_id = request.POST.get('item_id')

                if not item_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'Item ID is required'
                    }, status=400)
                
                order_item = get_object_or_404(OrderItem, id=item_id)
                order = order_item.order

                if order.is_returned:
                    return JsonResponse({
                        'success': False,
                        'message': 'Order has already been returned'
                    }, status=400)
                
                order_item.return_status = OrderItem.RETURN_COMPLETED
                order_item.is_returned = True
                order_item.save()

                refund_amount = order_item.price * order_item.quantity
                
                user = order.user
            
            try:
                wallet, created = Wallet.objects.get_or_create(
                    user=user,
                    defaults={'balance': Decimal(refund_amount)}
                )
                
                if not created:
                    wallet.balance += Decimal(refund_amount)
                    wallet.save()
                
                # Create wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_amount=refund_amount,
                    transaction_type='refund',
                    description=f'Refund for returned item in order #{order.id}'
                )
                
                # Check if all items in the order are returned
                all_items = OrderItem.objects.filter(order=order)
                returned_items = OrderItem.objects.filter(order=order, is_returned=True)
                
                if all_items.count() == returned_items.count():
                    order.order_status = 'Returned'
                    order.is_returned = True
                    order.return_status = order.RETURN_COMPLETED
                    order.return_date = timezone.now()
                    order.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Item return approved and refund processed to user wallet'
                })
                
            except Exception as e:
                # Rollback item status changes if refund fails
                order_item.return_status = OrderItem.RETURN_REQUESTED
                order_item.is_returned = False
                order_item.save()
                raise e
                
        except Exception as e:
            logger.error(f"Error in approve_item_return_request: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@login_required(login_url='adminlog')
def reject_item_return_request(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied: admin privileges required")
        return redirect('adminlog')
    
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                item_id = data.get('item_id')
            else:
                item_id = request.POST.get('item_id')
            
            if not item_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Order Item ID is required'
                }, status=400)
            
            order_item = get_object_or_404(OrderItem, id=item_id)

            if order_item.is_returned:
                return JsonResponse({
                    'success': False,
                    'message': 'Item has already been returned'
                }, status=400)
            
            # Update the item status
            order_item.return_status = OrderItem.RETURN_REJECTED
            order_item.return_reason = None
            order_item.save()

            return JsonResponse({
                'success': True,
                'message': 'Item return request rejected successfully'
            })
        except Exception as e:
            logger.error(f"Error in reject_item_return_request: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)



from django.db import transaction
@login_required
@transaction.atomic
def process_cancellation_request(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied: Admin privileges required")
        return redirect('adminlog')
    
    if request.method == 'POST':
        try:
            # Parse request data
            try:
                data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
                order_id = data.get('order_id')
                action = data.get('action')
            except Exception as e:
                logger.error(f"Error parsing request data: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid request data'
                }, status=400)

            # Validate required fields
            if not order_id or not action:
                return JsonResponse({
                    'success': False,
                    'message': 'Order ID and action are required'
                }, status=400)

            # Lock the order row for update
            order = Order.objects.select_for_update().get(id=order_id)
            
            logger.info(f"Processing cancellation for order {order.id}. Current status: {order.order_status}")

            # Validate order state
            if order.is_cancelled:
                return JsonResponse({
                    'success': False,
                    'message': 'Order has already been cancelled'
                }, status=400)
                
            if order.cancel_request_status != 'Requested':
                return JsonResponse({
                    'success': False,
                    'message': 'No cancellation request found for this order'
                }, status=400)

            if action == 'approve':
                # Process inventory return
                order_items = order.items.select_related('product_variation').all()
                for item in order_items:
                    if item.product_variation:
                        item.product_variation.stock += item.quantity
                        item.product_variation.save()
                    item.is_cancelled = True
                    item.save()

                # Update order status
                order.order_status = 'Cancelled'
                order.is_cancelled = True
                order.canceled_date = timezone.now()
                order.cancel_request_status = 'Approved'

                
                if order.payment_status == 'PAID' and order.payment_method in ['Razorpay', 'Wallet']:
                    try:
                        refund_amount = Decimal(str(order.total_amount))
                        logger.info(f"Processing refund of {refund_amount} for order {order.id}")

                        # Get or create wallet with lock
                        wallet, created = Wallet.objects.select_for_update().get_or_create(
                            user=order.user,
                            defaults={'balance': Decimal('0.00')}
                        )

                        # Log wallet state before update
                        logger.info(f"Wallet balance before: {wallet.balance}")

                        # Update wallet balance
                        wallet.balance += refund_amount
                        wallet.save()

                        # Create transaction record
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_amount=refund_amount,
                            transaction_type='refund',
                            description=f'Refund for cancelled order #{order.id}',
                            status='Completed'
                        )

                        # Update order payment status
                        order.payment_status = 'Refunded'
                        order.refund_amount = refund_amount
                        order.refund_date = timezone.now()

                        logger.info(f"Successfully refunded {refund_amount} to user {order.user.id} wallet")

                    except Exception as e:
                        logger.error(f"Refund processing failed: {str(e)}", exc_info=True)
                        # Continue with cancellation even if refund fails
                        order.payment_status = 'Refund Failed'
                        order.save()
                        raise  # Will trigger transaction rollback

                order.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Cancellation approved and processed',
                    'refund_processed': order.payment_status == 'Refunded'
                })
                
            elif action == 'reject':
                order.cancel_request_status = 'Rejected'
                order.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Cancellation request rejected'
                })
                
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid action. Must be "approve" or "reject"'
                }, status=400)
                
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            }, status=404)
            
        except Exception as e:
            logger.error(f"Error processing cancellation: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while processing the request'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

def coupon_management(request):
    
    if not request.user.is_superuser:
        messages.error(request, "Access denied: Admin privileges required")
        return redirect('adminlog')
    
    
    all_coupons = coupon.objects.all().order_by('-valid_from')

    page_number = request.GET.get('page', 1)
    paginator_obj = Paginator(all_coupons, 10)  # Use a different variable name
    page_obj = paginator_obj.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == "POST":
            data = json.loads(request.body)
            action = data.get('action')
            
            
            if action == 'add':
                try:
                    
                    coupon_code = data.get('couponCode', '').upper()
                    
                    if coupon.objects.filter(coupon_code=coupon_code).exists():
                        return JsonResponse({'status': 'error', 'message': 'Coupon code already exists'}, status=400)
                    
                    new_coupon = coupon(
                        coupon_code=coupon_code,
                        description=data.get('description', ''),
                        discount_type=data.get('discountType'),
                        discount_value=data.get('discountValue'),
                        min_order_amount=data.get('minCartValue') or None,
                        max_discount_value=data.get('maxDiscountValue') or None,
                        valid_from=datetime.strptime(data.get('validFrom'), '%Y-%m-%d'),
                        valid_to=datetime.strptime(data.get('validUntil'), '%Y-%m-%d'),
                        usage_limit=data.get('usageLimit') or None,
                        is_active=data.get('isActive') == 'true'
                    )
                    new_coupon.save()
                    return JsonResponse({'status': 'success', 'message': 'Coupon added successfully'})
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
            # Update existing coupon
            elif action == 'update':
                try:
                    coupon_id = data.get('couponId')
                    coupon_obj = coupon.objects.get(id=coupon_id)
                    
                    # Convert coupon code to uppercase
                    coupon_code = data.get('couponCode', '').upper()
                    
                    # Check if another coupon already has this code
                    if coupon.objects.filter(coupon_code=coupon_code).exclude(id=coupon_id).exists():
                        return JsonResponse({'status': 'error', 'message': 'Coupon code already exists'}, status=400)
                    
                    coupon_obj.coupon_code = coupon_code
                    coupon_obj.description = data.get('description', '')
                    coupon_obj.discount_type = data.get('discountType')
                    coupon_obj.discount_value = data.get('discountValue')
                    coupon_obj.min_order_amount = data.get('minCartValue') or None
                    coupon_obj.max_discount_value = data.get('maxDiscountValue') or None
                    coupon_obj.valid_from = datetime.strptime(data.get('validFrom'), '%Y-%m-%d')
                    coupon_obj.valid_to = datetime.strptime(data.get('validUntil'), '%Y-%m-%d')
                    coupon_obj.usage_limit = data.get('usageLimit') or None
                    coupon_obj.is_active = data.get('isActive')
                    
                    coupon_obj.save()
                    return JsonResponse({'status': 'success', 'message': 'Coupon updated successfully'})
                except coupon.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Coupon not found'}, status=404)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
            # Delete coupon
            elif action == 'delete':
                try:
                    coupon_id = data.get('couponId')
                    coupon_obj = coupon.objects.get(id=coupon_id)
                    coupon_obj.delete()
                    return JsonResponse({'status': 'success', 'message': 'Coupon deleted successfully'})
                except coupon.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Coupon not found'}, status=404)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
            # Toggle coupon status
            elif action == 'toggle_status':
                try:
                    coupon_id = data.get('couponId')
                    coupon_obj = coupon.objects.get(id=coupon_id)
                    coupon_obj.is_active = not coupon_obj.is_active
                    coupon_obj.save()
                    return JsonResponse({
                        'status': 'success', 
                        'message': f'Coupon {"activated" if coupon_obj.is_active else "deactivated"} successfully',
                        'is_active': coupon_obj.is_active
                    })
                except coupon.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Coupon not found'}, status=404)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    context = {
        'coupons': page_obj,
        'currentPage': int(page_number),
        'totalPages': paginator_obj.num_pages 
    }
    return render(request, 'couponManagement.html', context)
    

# #########################################################offer managemnt###########################################################


@login_required(login_url='adminlog')
def offer_management(request):
    
    offers_list = OfferTable.objects.all().order_by('-created_at')
    
   
    paginator = Paginator(offers_list, 10) 
    page_number = request.GET.get('page', 1)
    offers = paginator.get_page(page_number)
    
    
    products = ProductTable.objects.filter(is_active=True)
    brands = BrandTable.objects.all()
    
    context = {
        'offers': offers,
        'products': products,
        'brands': brands,
        'currentPage': int(page_number),
        'totalPages': paginator.num_pages,
    }
    
    return render(request, 'offerManagement.html', context)

@login_required
def add_offer(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            required_fields = ['offer_name', 'offer_type', 'discount_type', 'discount_value', 'valid_from', 'valid_to']
            for field in required_fields:
                if not data.get(field):
                     return JsonResponse({'success': False, 'message': f'{field.replace("_", " ").title()} is required'})
            
            try:
                discount_value = float(data.get('discount_value'))
                if discount_value <= 0:
                    return JsonResponse({'success': False, 'message': 'Discount value must be greater than 0'})
                
                if data['discount_type'] == 'percentage' and discount_value > 100:
                    return JsonResponse({'success': False, 'message': 'Percentage discount cannot exceed 100%'})

            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid discount value'})   

            try:
                
                valid_from = timezone.make_aware(datetime.fromisoformat(data['valid_from'].replace('Z', '')))
                valid_to = timezone.make_aware(datetime.fromisoformat(data['valid_to'].replace('Z', '')))
                
                now = timezone.now()
                
                if valid_to <= valid_from:
                    return JsonResponse({'success': False, 'message': 'End date must be after start date'})
                
                if valid_to < now:
                    return JsonResponse({'success': False, 'message': 'End date cannot be in the past'})
                    
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid date format'})
            
           
            if data['offer_type'] == 'product' and not data.get('product_id'):
                return JsonResponse({'success': False, 'message': 'Product is required for product offers'})
            elif data['offer_type'] == 'brand' and not data.get('brand_id'):
                return JsonResponse({'success': False, 'message': 'Brand is required for brand offers'})

            
            offer_name = data.get('offer_name', f"{data['offer_type'].title()} Offer - {timezone.now().date()}")
            offer_type = data.get('offer_type')
            discount_type = data.get('discount_type')
            discount_value = data.get('discount_value')
            is_active = data.get('is_active', False)
            
            
            new_offer = OfferTable(
                offer_name=offer_name,
                offer_type=offer_type,
                discount_type=discount_type,
                discount_value=discount_value,
                valid_from=valid_from,
                valid_to=valid_to,
                description=data.get('description', ''),
                is_active=is_active
            )
            
           
            if data['offer_type'] == 'product':
                product = get_object_or_404(ProductTable, product_id=data['product_id'])
                new_offer.product = product
            else:
                brand = get_object_or_404(BrandTable, brand_id=data['brand_id'])
                new_offer.brand = brand
            
            new_offer.save()
            
            return JsonResponse({'success': True, 'message': 'Offer added successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def update_offer(request, offer_id):
    if request.method == 'POST':
        try:
            offer = get_object_or_404(OfferTable, id=offer_id)
            data = json.loads(request.body)
            
            # Required fields validation
            required_fields = ['discount_type', 'discount_value', 'valid_from', 'valid_to']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'success': False, 'message': f'{field.replace("_", " ").title()} is required'})
            
            # Numeric validation
            try:
                discount_value = float(data['discount_value'])
                if discount_value <= 0:
                    return JsonResponse({'success': False, 'message': 'Discount value must be positive'})
                
                if data['discount_type'] == 'percentage' and discount_value > 100:
                    return JsonResponse({'success': False, 'message': 'Percentage discount cannot exceed 100%'})
                    
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid discount value'})
            
            # Date validation
            try:
                # Parse the input dates and make them timezone-aware
                valid_from = timezone.make_aware(datetime.fromisoformat(data['valid_from'].replace('Z', '')))
                valid_to = timezone.make_aware(datetime.fromisoformat(data['valid_to'].replace('Z', '')))
                
                now = timezone.now()
                
                if valid_to <= valid_from:
                    return JsonResponse({'success': False, 'message': 'End date must be after start date'})
                
                if valid_to < now:
                    return JsonResponse({'success': False, 'message': 'End date cannot be in the past'})
                    
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid date format'})
            
            # Update offer
            offer.offer_name = data.get('offer_name', offer.offer_name)
            offer.discount_type = data['discount_type']
            offer.discount_value = discount_value
            offer.valid_from = valid_from
            offer.valid_to = valid_to
            offer.description = data.get('description', offer.description)
            offer.max_discount_amount = data.get('max_discount_amount')
            offer.min_cart_value = data.get('min_cart_value', 0)
            
            offer.save()
            
            return JsonResponse({'success': True, 'message': 'Offer updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def toggle_offer_status(request, offer_id):
    if request.method == 'POST':
        try:
            offer = get_object_or_404(OfferTable, id=offer_id)
            offer.is_active = not offer.is_active
            offer.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Offer status updated successfully',
                'status': 'active' if offer.is_active else 'inactive'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def delete_offer(request, offer_id):
    if request.method == 'DELETE':
        try:
            offer = get_object_or_404(OfferTable, id=offer_id)
            offer.delete()
            
            return JsonResponse({'success': True, 'message': 'Offer deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_entities_by_type(request):
    offer_type = request.GET.get('type')
    
    if offer_type == 'product':
        products = ProductTable.objects.filter(is_active=True)
        entities = [{'id': product.product_id, 'name': product.product_name} for product in products]
    elif offer_type == 'brand':
        brands = BrandTable.objects.all()
        entities = [{'id': brand.brand_id, 'name': brand.brand_name} for brand in brands]
    else:
        entities = []
    
    return JsonResponse({'entities': entities})



@never_cache
def adminlogout(request):
    logout(request)
    response = redirect('adminlog')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response
