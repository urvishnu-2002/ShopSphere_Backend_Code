from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login ,logout
from django.shortcuts import render, redirect, get_object_or_404
from .models import AuthUser, Product, Cart, CartItem, Order, OrderItem
from .serializers import RegisterSerializer, ProductSerializer, CartSerializer, OrderSerializer


# 🔹 REGISTER
@api_view(['GET', 'POST'])
def register_api(request):
    if request.method == 'GET':
        return render(request, "user_register.html")
    
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        if 'application/json' in request.headers.get('Accept', ''):
            return Response({"message": "User registered successfully"}, status=201)
        return redirect('login')

    return Response(serializer.errors, status=400)


# 🔹 LOGIN (JWT token generate)
@api_view(['GET', 'POST'])
def login_api(request):
    if request.method == 'GET':
        return render(request, "user_login.html")
    
    # We use email as the primary login field now
    email = request.data.get('email') or request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=email, password=password)

    if user:
        # Use session login for HTML form submissions
        login(request, user)
        
        # For API/JSON clients, also return JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Check if it's HTML form submission vs JSON API
        if 'application/json' in request.headers.get('Accept', ''):
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "username": user.username,
                "role": user.role
            })
        else:
            return redirect('home')

    return Response({"error": "Invalid credentials"}, status=401)


# 🔹 HOME (Product Page)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def home_api(request):
    products = Product.objects.all()
    
    # API / JSON Response
    if 'application/json' in request.headers.get('Accept', ''):
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
        
    # HTML Response
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            # Sum of quantities
            cart_count = sum(item.quantity for item in cart.items.all())
        except Cart.DoesNotExist:
            pass
            
    return render(request, "product_list.html", {
        "products": products, 
        "cart_count": cart_count,
        "user": request.user
    })

# 🔹 ADD TO CART
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    
    if 'application/json' in request.headers.get('Accept', ''):
        return Response({"message": "Item added to cart", "cart_count": cart.items.count()})
        
    return redirect('home')


# 🔹 VIEW CART
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    
    if 'application/json' in request.headers.get('Accept', ''):
        serializer = CartSerializer(cart)
        return Response(serializer.data)
        
    total_price = sum(item.total_price() for item in cart_items)
    
    return render(request, "cart.html", {
        "cart_items": cart_items, 
        "total_cart_price": total_price
    })


# 🔹 CHECKOUT
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def checkout_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    
    if not cart_items:
        if 'application/json' in request.headers.get('Accept', ''):
             return Response({"message": "Cart is empty"}, status=400)
        return redirect('cart')
        
    total_price = sum(item.total_price() for item in cart_items)
    items_count = sum(item.quantity for item in cart_items)
    
    if 'application/json' in request.headers.get('Accept', ''):
        return Response({
            "total_price": total_price,
            "items_count": items_count,
            "cart_items": CartSerializer(cart).data
        })
    
    return render(request, "checkout.html", {
        "total_price": total_price,
        "items_count": items_count
    })


# 🔹 PROCESS PAYMENT
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment(request):
    payment_mode = request.data.get('payment_mode')
    transaction_id = request.data.get('transaction_id')
    items_from_request = request.data.get('items') # For frontend direct sync
    
    if not payment_mode:
        if 'application/json' in request.headers.get('Accept', ''):
            return Response({"error": "Payment mode required"}, status=400)
        return redirect('checkout')

    created_orders = []
    
    # CASE 1: Items are passed directly in the request (Frontend Redux state)
    if items_from_request:
        for item_data in items_from_request:
            name = item_data.get('name')
            quantity = item_data.get('quantity', 1)
            price = item_data.get('price', 0)
            
            item_name_str = f"{quantity} x {name}"
            
            order = Order.objects.create(
                user=request.user,
                payment_mode=payment_mode,
                transaction_id=transaction_id,
                item_names=item_name_str
            )
            
            OrderItem.objects.create(
                order=order,
                product_name=name,
                quantity=quantity,
                price=price
            )
            created_orders.append(order)
            
        # Also clear the DB cart if it exists
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
            
    # CASE 2: Fallback to Backend Database Cart
    else:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
        except Cart.DoesNotExist:
            if 'application/json' in request.headers.get('Accept', ''):
                 return Response({"error": "Cart not found and no items provided"}, status=404)
            return redirect('home')
        
        if not cart_items:
            if 'application/json' in request.headers.get('Accept', ''):
                 return Response({"error": "Cart is empty"}, status=400)
            return redirect('home')
        
        for item in cart_items:
            item_name_str = f"{item.quantity} x {item.product.name}"
            
            order = Order.objects.create(
                user=request.user,
                payment_mode=payment_mode,
                transaction_id=transaction_id,
                item_names=item_name_str
            )
            
            OrderItem.objects.create(
                order=order,
                product_name=item.product.name,
                quantity=item.quantity,
                price=item.product.price
            )
            created_orders.append(order)
            item.delete()

    if 'application/json' in request.headers.get('Accept', ''):
        return Response({
            "success": True, 
            "message": "Payment successful", 
            "orders_created": len(created_orders)
        })
        
    return redirect('my_orders')


# 🔹 MY ORDERS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    
    if 'application/json' in request.headers.get('Accept', ''):
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
        
    return render(request, "my_orders.html", {"orders": orders})


# 🔹 LOGOUT
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    logout(request)
    return redirect('login')