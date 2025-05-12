
from .import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path


urlpatterns=[  
    path('admin/', views.adminhome, name='admin_home'),
    path('adminlog/', views.adminlog, name='adminlog'),
    path('adminapp/adminhome/', views.adminhome, name='adminhome'),
    path('adcategory/', views.admincategory, name='adcategory'),

    path('admin/products/toggle-status/<int:product_id>/', views.toggle_product_status, name='toggle_product_status'),
    path('admin/products/edit/<int:product_id>/', views.editproducts, name='editproduct'),

    path('admin/products/variance/<int:product_id>/', views.product_variance, name='product_variance'),
    path('admin/users/toggle-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('adcategory/toggle-status/<int:brand_id>/', views.toggle_category_status, name='toggle_category_status'),

    path('adcategory/edit/<int:brand_id>/', views.edit_category, name='edit_category'),
    

    path('adproducts/', views.adproductpage, name='adproducts'),
    path('editproducts/', views.editproducts, name='editproducts'),


    path('adusermanage/', views.adusermanage, name='adminuser'),


    path('ordermanagement/',views.ordermanagement,name='ordermanagement'),
    path('vieworder/', views.vieworder, name='vieworder'),
    path('admin/update_order_status/', views.update_order_status, name='update_order_status'),
    path('admin/approve_return_request/', views.approve_return_request, name='approve_return_request'),
    path('admin/reject_return_request/', views.reject_return_request, name='reject_return_request'),
    path('admin/process_cancellation_request/', views.process_cancellation_request, name='process_cancellation_request'),

     path('admin/approve_item_return_request/', views.approve_item_return_request, name='approve_item_return_request'),
    path('admin/reject_item_return_request/', views.reject_item_return_request, name='reject_item_return_request'),
   
    path('admin/offers/', views.offer_management, name='offer_management'),
    path('admin/offers/add', views.add_offer, name='add_offer'),
    path('admin/offers/update/<int:offer_id>', views.update_offer, name='update_offer'),
    path('admin/offers/toggle-status/<int:offer_id>', views.toggle_offer_status, name='toggle_offer_status'),
    path('admin/offers/delete/<int:offer_id>', views.delete_offer, name='delete_offer'),
    path('admin/offers/get-entities', views.get_entities_by_type, name='get_entities_by_type'),


    path('coupons/', views.coupon_management, name='coupon_management'),
    path('adlogout/',views.adminlogout,name='adlogout'),  

    
    path('admin/sales-report', views.sales_report, name='admin_sales_report'),
    path('admin/sales-chart-data', views.sales_chart_data, name='admin_sales_chart_data'),
    path('admin/best-selling-products', views.best_selling_products, name='admin_best_selling_products'),
    path('admin/best_selling_categories', views.best_selling_categories, name='admin_best_selling_categories'),

    path('admin/detailed-orders/', views.detailed_orders, name='admin_detailed_orders'),
    path('admin/order-items/', views.order_items, name='admin_order_items'),


]  
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)