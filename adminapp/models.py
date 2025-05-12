from django.db import models
from authentication1.models import usertable
from django.core.validators import MinValueValidator
from decimal import Decimal
from authentication1.models import usertable
from django.utils.timezone import now
from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator

class Gender(models.Model):
    gender_id = models.BigAutoField(primary_key=True)
    gender = models.CharField(max_length=225, unique=True)
    
    def __str__(self):
        return self.gender


class Occasion(models.Model):
    occasion_id = models.BigAutoField(primary_key=True)
    occasion = models.CharField(max_length=225, unique=True)
    
    def __str__(self):
        return self.occasion
    


class SizeTable(models.Model):
    size_id = models.BigAutoField(primary_key=True)
    size = models.IntegerField(unique=True)
    
    def __str__(self):
        return f"{self.size} ml"


class Fragrance(models.Model):
    fragrance_id = models.BigAutoField(primary_key=True)
    fragrance_type = models.CharField(max_length=225, unique=True)
    
    def __str__(self):
        return self.fragrance_type
    


class BrandTable(models.Model):
    brand_id = models.BigAutoField(primary_key=True)
    brand_name = models.CharField(max_length=225, unique=True)
    
    def __str__(self):
        return self.brand_name
    


class ConcentrationType(models.Model):
    concentration_id = models.BigAutoField(primary_key=True)
    concentration = models.CharField(max_length=225, unique=True)
    
    def __str__(self):
        return self.concentration
    


class ProductTable(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=225)
    description = models.TextField(null=True, blank=True)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, related_name='products')
    occasion = models.ForeignKey(Occasion, on_delete=models.CASCADE, related_name='products')
    fragrance = models.ForeignKey(Fragrance, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(BrandTable, on_delete=models.CASCADE, related_name='products')
    concentration = models.ForeignKey(ConcentrationType, on_delete=models.CASCADE, related_name='products')
    is_active = models.BooleanField(default=True)

    @property
    def total_stock(self):
        return sum(variance.stock for variance in self.varience.all())

    @property
    def isOutOfStock(self):
        return self.total_stock == 0
    
    def __str__(self):
        return f"{self.product_name} - {self.brand.brand_name}"
    
class VarienceTable(models.Model):
    product = models.ForeignKey(ProductTable, on_delete=models.CASCADE, related_name='varience')
    size = models.ForeignKey(SizeTable, on_delete=models.CASCADE, related_name='varience')
    stock = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def get_final_price(self):
        """Get the final price after applying any active offers"""
        final_price = self.price
        now = timezone.now()
        
        # Check for product-specific offers first
        product_offers = self.product.product_offers.filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        ).first()
        
        if product_offers:
            return product_offers.calculate_discounted_price(self.price)
        
        # If no product offers, check for brand offers
        brand_offers = self.product.brand.brand_offers.filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        ).first()
        
        if brand_offers:
            return brand_offers.calculate_discounted_price(self.price)
            
        return final_price
    
 ####################################offer tabele#######################################  

class OfferTable(models.Model):
    offer_name = models.CharField(max_length=50)
    OFFER_TYPES = [
        ('brand', 'Brand Offer'),
        ('product', 'Single Product Offer'),
    ]
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES)
    product = models.ForeignKey(ProductTable, on_delete=models.CASCADE, null=True, blank=True, related_name='product_offers')
    brand = models.ForeignKey(BrandTable, on_delete=models.CASCADE, null=True, blank=True, related_name='brand_offers')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Offer {self.offer_name}"
    
    def calculate_discounted_price(self, original_price):
        
        if not self.is_active or not (self.valid_from <= timezone.now() <= self.valid_to):
            return original_price
            
        if self.discount_type == 'percentage':
            return original_price * (1 - self.discount_value / 100)
        elif self.discount_type == 'fixed':
            return max(0, original_price - self.discount_value)
        return original_price

# #################################### coupon table#######################################

class coupon(models.Model):
    coupon_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(max_length=20, choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2 ,null=True, blank=True)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=False)


# ############################################ Product Image Table ###########################################

class ProductImage(models.Model):
    image_id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey(ProductTable, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='perfume_images/', null=True, blank=True)
    
    
    def __str__(self):
        return f"{self.product.product_name}"


class Cart(models.Model):
    user = models.ForeignKey(usertable, on_delete=models.CASCADE, related_name='cart')
    applied_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    applied_coupon = models.CharField(max_length=50, null=True, blank=True)
    stored_vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    @property
    def total_price(self):
         return sum(Decimal(str(item.total_price)) for item in self.items.all())
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def vat_amount(self):
        return self.stored_vat_amount
    
    @property
    def final_total(self):
      return Decimal(str(self.total_price)) - Decimal(str(self.applied_discount)) + Decimal(str(self.vat_amount))

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('ProductTable', on_delete=models.CASCADE)
    variance = models.ForeignKey('VarienceTable', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
   
    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} ({self.variance.size.size}ml)"
    
    @property
    def total_price(self):
        return self.variance.get_final_price() * self.quantity
    



# #################################################### Wallet and Transaction Models ###################################################
class Wallet(models.Model):
    wallet_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(usertable, on_delete=models.CASCADE)
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    def __str__(self):
        return f"Wallet {self.wallet_id} - User {self.user_id} (Balance: {self.balance})"
    
class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('add', 'Added to wallet'),
        ('deduct', 'Deducted from wallet'),
        ('refund', 'Refunded'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    description = models.TextField(blank=True, null=True)
    transaction_time = models.DateTimeField(default=now)

    def __str__(self):
        return f"Transaction: {self.transaction_type} - {self.transaction_amount} on {self.transaction_time}"
    
class Wishlist(models.Model):
    user = models.ForeignKey(usertable, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(ProductTable, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.username}'s wishlist item: {self.product.product_name}"
    
class review(models.Model):
    user = models.ForeignKey(usertable, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(ProductTable, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(default=0)
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.get_full_name()} for {self.product.product_name}"