from django.db import models
from authentication1.models import usertable
from userprofile.models import UserAddress
from decimal import Decimal
from django.utils import timezone
from datetime import datetime
from adminapp.models import Cart, VarienceTable,BrandTable,Wallet,WalletTransaction,ProductTable

from decimal import Decimal, ROUND_HALF_UP

class Order(models.Model):
    # All your existing model fields remain the same
    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Returned', 'Returned'),
        ('Cancelled', 'Cancelled')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('PAID', 'PAID'),
        ('failed', 'failed'),
        ('Retry', 'Retry'), 
        ('Refunded', 'Refunded')
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('Razorpay', 'Razorpay'),
        ('Wallet', 'Wallet'),
        ('Cash on Delivery', 'Cash on Delivery')
    ]

    CANCEL_REQUEST_CHOICES = [
        ('Requested', 'Cancellation Requested'),
        ('Approved', 'Cancellation Approved'),
        ('Rejected', 'Cancellation Rejected')
    ]

    user = models.ForeignKey(usertable, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # New fields to store cart calculations at order time
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    shipping_address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True, related_name='orders')
    delivery_address = models.TextField(null=True, blank=True)  
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='Cash on Delivery')
    is_coupon_applied = models.BooleanField(default=False)
    is_offer_applied = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)

    # Rest of your model fields
    RETURN_REQUESTED = 'Requested'
    RETURN_APPROVED = 'Approved'
    RETURN_REJECTED = 'Rejected'
    RETURN_COMPLETED = 'Completed'
    
    RETURN_STATUS_CHOICES = [
        (RETURN_REQUESTED, 'Return Requested'),
        (RETURN_APPROVED, 'Return Approved'),
        (RETURN_REJECTED, 'Return Rejected'),
        (RETURN_COMPLETED, 'Return Completed'),
    ]
    
    return_status = models.CharField(
        max_length=20, 
        choices=RETURN_STATUS_CHOICES, 
        null=True, 
        blank=True
    )
    return_request_date = models.DateTimeField(null=True, blank=True)
    return_completion_date = models.DateTimeField(null=True, blank=True)
    return_reason = models.TextField(null=True, blank=True)
    
    return_date = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_returned = models.BooleanField(default=False)
    
    cancel_request_status = models.CharField(max_length=20, choices=CANCEL_REQUEST_CHOICES, null=True, blank=True)
    cancel_request_date = models.DateTimeField(null=True, blank=True)

    is_cancelled = models.BooleanField(default=False)
    refund_date = models.DateTimeField(null=True, blank=True)
    canceled_date = models.DateTimeField(null=True, blank=True)
    cancel_description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        if hasattr(self, 'id'):
            return f"Order #{self.id} - {self.user.username if self.user else 'No user'}"
        return "New Order"
    
    def save(self, *args, **kwargs):
        # If this is a new order (no ID yet), calculate and store totals from cart
        if not self.pk and self.cart:
            # Store cart calculations in order
            self.subtotal = self.cart.total_price
            self.discount_amount = self.cart.applied_discount
            self.vat_amount = self.cart.stored_vat_amount
            # Calculate grand total
            self.grand_total = (self.subtotal - self.discount_amount + 
                               self.vat_amount)
            # Set total_amount to match subtotal for backward compatibility
            self.total_amount = self.subtotal
        
        super().save(*args, **kwargs)
    
    @property
    def is_completed(self):
        return self.order_status == 'Delivered' and self.payment_status == 'Completed'
    
    @property
    def days_since_order(self):
        if self.order_date:
            now = datetime.now()
            delta = now - self.order_date.replace(tzinfo=None)
            return delta.days
        return None
    
    @property
    def current_subtotal(self):
        """Calculate the current subtotal based on active order items only and round to 2 decimal places"""
        subtotal = sum(Decimal(str(item.total_price)) for item in self.items.all() if not item.is_cancelled)
        return subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def calculate_grand_total(self):
        """Calculate grand total without considering cancelled items and round to 2 decimal places"""
        # Apply proportional discount based on remaining items
        if self.subtotal > 0:
            # Calculate what percentage of the original order remains
            remaining_ratio = self.current_subtotal / self.subtotal
            # Apply the same ratio to the discount and round
            current_discount = (self.discount_amount * remaining_ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            current_discount = Decimal('0.00')
            
        # Calculate VAT on the current subtotal and round
        if self.vat_amount > 0 and self.subtotal > 0:
            vat_rate = self.vat_amount / self.subtotal
            current_vat = (self.current_subtotal * vat_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            current_vat = Decimal(self.vat_amount) if not isinstance(self.vat_amount, Decimal) else self.vat_amount
            
        # Calculate and round the final result
        total = self.current_subtotal - current_discount + current_vat
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
    @property
    def get_grand_total(self):
        """
        Return the dynamically calculated grand total based on active items
        """
        return self.calculate_grand_total
        
    @property
    def get_current_discount(self):
        """Get the proportional discount for active items, rounded to 2 decimal places"""
        if self.subtotal > 0 and self.discount_amount > 0:
            remaining_ratio = self.current_subtotal / self.subtotal
            return (self.discount_amount * remaining_ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return Decimal('0.00')
        
    @property
    def get_current_vat(self):
        """Get the VAT amount for active items, rounded to 2 decimal places"""
        if self.vat_amount > 0 and self.subtotal > 0:
            vat_rate = self.vat_amount / self.subtotal
            return (self.current_subtotal * vat_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        vat_val = Decimal(self.vat_amount) if not isinstance(self.vat_amount, Decimal) else self.vat_amount
        return vat_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)    

class OrderItem(models.Model):
    
    RETURN_REQUESTED = 'Requested'
    RETURN_APPROVED = 'Approved'
    RETURN_REJECTED = 'Rejected'
    RETURN_COMPLETED = 'Completed'
    
    RETURN_STATUS_CHOICES = [
        (RETURN_REQUESTED, 'Return Requested'),
        (RETURN_APPROVED, 'Return Approved'),
        (RETURN_REJECTED, 'Return Rejected'),
        (RETURN_COMPLETED, 'Return Completed'),
    ]
    
    # Core fields
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variation = models.ForeignKey(VarienceTable, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    is_returned = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    return_reason = models.TextField(null=True, blank=True)
    return_status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, null=True, blank=True)
    
    def __str__(self):
        product_name = "Unknown"
        if self.product_variation and hasattr(self.product_variation, 'product'):
            product_name = self.product_variation.product.product_name
        return f"{self.quantity}x {product_name} in Order #{self.order.id}"
    
    @property
    def total_price(self):
        return self.price * self.quantity