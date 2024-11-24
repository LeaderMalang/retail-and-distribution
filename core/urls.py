from django.urls import path
from . import views

urlpatterns = [
    path('create_order_with_products/', views.create_order_with_products, name='create_order_with_products'),
    path('order_list/', views.order_list, name='order_list'),
    path('create_order/', views.create_order, name='create_order'),
    path('api/orders/', views.create_api_order, name='create_api_order'),
]
