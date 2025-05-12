from django.urls import path
from .import views



urlpatterns = [
    
    path('userprofile/',views.userprofile,name='userprofile'),  
    path('myaccount/',views.myaccount,name='myaccount'),
    path('myaddress/',views.address,name='address'),
    path('editaddress/',views.editaddress,name='editaddress'),
    path('editaddress/<int:address_id>/', views.editaddress, name='editaddress'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('set-default-address/',views.set_default_address, name='set_default_address'),


    path('wallet-transactions/', views.wallet_transactions, name='wallet_transactions'),
    path('wallet/add-money/', views.add_money, name='add_money'),
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),

    path('payment-success/', views.payment_success, name='payment_success'),
    path('payments/retry/', views.retry_payment, name='retry_payment'),
    
    

    path('myorders/', views.order_list, name='myorders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('order-items/<int:item_id>/cancel/', views.cancel_order_item, name='cancel_order_item'),
    path('orders/<int:order_id>/request-return/', views.request_return, name='request_return'),
    path('orders/<int:order_id>/download-invoice/', views.download_invoice, name='download_invoice'),
    path('orders/<int:order_id>/retry-payment/',views.retry_payment, name='retry_payment'),
    path('order-items/<int:item_id>/request-return/', views.request_item_return, name='request_item_return'),

    
    path('mypass/',views. mypassword,name='mypassword')
] 
