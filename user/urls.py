from django.urls import path
from . import views
from .views import singleproduct
# from .views import PerfumeChatbotView
urlpatterns = [
    # Basic pages
    path('', views.nohome, name='nohome'),
    path('home/', views.home, name='home'),
    path('myshop/', views.myshop, name='myshop'),
    path('product/<int:product_id>/', views.singleproduct, name='singleproduct'),
    path('test/', views.loadtest, name='test'),

    # Wishlist related URLs
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Cart related URLs
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('remove-cart-item/', views.remove_cart_item, name='remove_cart_item'),
    path('get-cart-count/', views.get_cart_count, name='get_cart_count'),
    path('api/product-variances/<int:product_id>/', views.get_product_variances, name='get_product_variances'),

     path('product/<int:product_id>/review/',views.submit_review, name='submit_review'), 
     path('get-product-reviews/<str:product_id>/',views.get_product_reviews, name='get_product_reviews'),

    # Checkout and payment related URLs
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders/<int:order_id>/retry_payment/', views.retry_payment, name='retry_payment'),

    # Address management
    path('update-address/', views.update_address, name='update_address'),
    path('save-address/', views.save_address, name='save_address'),

    # Coupon related URLs
    path('get-available-coupons/', views.get_available_coupons, name='get_available_coupons'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),

    # Razorpay payment URLs
    path('razorpay-payment-cancel/', views.razorpay_payment_cancel, name='razorpay_payment_cancel'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('update-payment-status/', views.update_payment_status, name='update_payment_status'),


    path('best-selling-products', views.best_selling_products3, name='best_selling_products'), 
    # API endpoints
    path('api/order-status/<int:order_id>/', views.order_status_api, name='order_status_api'),

    # path('api/chatbot/', PerfumeChatbotView.as_view(), name='perfume_chatbot'),
    # path('test-openai/', views.test_openai, name='test_openai'),

    path('contact/', views.contact, name='contact'),

]