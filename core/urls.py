from django.urls import path
from . import views

urlpatterns = [
    path('create_order_with_products/', views.create_order_with_products, name='create_order_with_products'),
    path('order_list/', views.order_list, name='order_list'),
    path('create_order/', views.create_order, name='create_order'),
    path('api/orders/', views.create_api_order, name='create_api_order'),
    path('api/orders/<int:order_id>/', views.update_api_order, name='update_api_order'),
    path('api/orders/<int:order_id>/', views.delete_api_order, name='delete_api_order'),
    path('order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('update_order/<int:order_id>/', views.update_order, name='update_order'),
    
    path('api/purchase_order/', views.create_api_purchase_order, name='create_api_purchase_order'),
    path('api/purchase_order/<int:order_id>/', views.update_api_purchase_order, name='update_api_purchase_order'),
    path('api/purchase_order/<int:order_id>/', views.delete_api_purchase_order, name='delete_api_purchase_order'),

    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('sale_order/', views.create_sale_order, name='create_sale_order'),
    path('sale_order/<int:order_id>/', views.update_sale_order, name='update_sale_order'),
    path('sale_order_list/', views.sale_order_list, name='sale_order_list'),


    path('purchase_order/', views.create_purchase_order, name='create_purchase_order'),
    path('purchase_order/<int:order_id>/', views.update_purchase_order, name='update_purchase_order'),
    path('purchase_order_list/', views.purchase_order_list, name='purchase_order_list'),
]
