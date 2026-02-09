from django.urls import path
from django.http import HttpResponse
from . import views

urlpatterns = [
    path('', lambda request: HttpResponse("ShopSphere Backend is running 🚀")),
    path('register/', views.register_api, name='register'),
    path('login', views.login_api, name='login'),
    path('home', views.home_api, name='home'),
    path('logout', views.logout_api, name='logout'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('process_payment/', views.process_payment, name='process_payment'),
    path('my_orders/', views.my_orders, name='my_orders'),
    path('address/', views.address_page, name="address_page"),
    path('delete-address/<int:id>/', views.delete_address, name="delete_address"),
]