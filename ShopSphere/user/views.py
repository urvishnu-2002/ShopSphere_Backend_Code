from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import AuthUser, Product, Cart, CartItem, Order, OrderItem, Address
from .serializers import RegisterSerializer, ProductSerializer, CartItemSerializer, OrderSerializer
from .forms import AddressForm

# 🔹 REGISTER
@api_view(['GET', 'POST'])
def register_api(request):
    if request.method == 'GET':
        return render(request, "user_register.html")
    
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        if request.accepted_renderer.format == 'json':
            return Response({"message": "User registered successfully"}, status=201)
        return redirect('login')
    
    return Response(serializer.errors, status=400)

# 🔹 LOGIN (JWT token generate)
@api_view(['GET', 'POST'])
def login_api(request):
    if request.method == 'GET':
        return render(request, "user_login.html")
    
    # support both JSON API clients (username) and HTML form (email)
    username = request.data.get('email') or request.data.get('username')
    password = request.data.get('password')

    # If user provided an email, resolve to username
    if username and '@' in username:
        try:
            u = AuthUser.objects.get(email=username)
            username = u.username
        except AuthUser.DoesNotExist:
            username = None
    user = authenticate(username=username, password=password)
    if user:
        # Use session login for HTML form submissions
        login(request, user)
        
        # For API/JSON clients, also return JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Check if it's HTML form submission vs JSON API
        if request.accepted_renderer.format == 'json':
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "username": user.username,
                "role": user.role
            })
        else:
            # HTML form: redirect to home
            return redirect('home')
    return Response({"error": "Invalid credentials"}, status=401)

# 🔹 HOME (Product Page)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def home_api(request):
    products = Product.objects.all()
    
    # API / JSON Response
    if request.accepted_renderer.format == 'json':
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
    
    if request.accepted_renderer.format == 'json':
        return Response({"message": "Item added to cart", "cart_count": cart.items.count()})
        
    return redirect('home')


# 🔹 VIEW CART
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    
    if request.accepted_renderer.format == 'json':
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
        if request.accepted_renderer.format == 'json':
             return Response({"message": "Cart is empty"}, status=400)
        return redirect('cart')
        
    total_price = sum(item.total_price() for item in cart_items)
    items_count = sum(item.quantity for item in cart_items)
    
    if request.accepted_renderer.format == 'json':
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
    items_data = request.data.get('items')

    if not payment_mode:
        return Response({"error": "Payment mode required"}, status=400)

    # 1. Get items to order
    items_to_process = []
    
    if items_data:
        items_to_process = items_data
    else:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
            if not cart_items:
                 return Response({"error": "Cart is empty"}, status=400)
            
            for item in cart_items:
                items_to_process.append({
                    "name": item.product.name,
                    "quantity": item.quantity,
                    "price": float(item.product.price)
                })
            cart.items.all().delete()
        except Cart.DoesNotExist:
            return Response({"error": "No cart items found"}, status=400)

    if not items_to_process:
        return Response({"error": "No items to process"}, status=400)

    # 2. Create ONE Order for the entire transaction
    # Summary of items for the summary field
    summary_str = ", ".join([f"{i.get('quantity')} x {i.get('name')}" for i in items_to_process])

    order = Order.objects.create(
        user=request.user,
        payment_mode=payment_mode,
        transaction_id=transaction_id,
        item_names=summary_str
    )

    # 3. Create all OrderItems linked to this one order
    for item in items_to_process:
        OrderItem.objects.create(
            order=order,
            product_name=item.get('name', 'Product'),
            quantity=item.get('quantity', 1),
            price=item.get('price', 0)
        )
        
    return Response({
        "message": "Payment successful and order recorded", 
        "order_id": order.id,
        "transaction_id": transaction_id
    }, status=201)


# 🔹 MY ORDERS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    
    if request.accepted_renderer.format == 'json':
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
        
    return render(request, "my_orders.html", {"orders": orders})

# 🔹 LOGOUT
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    logout(request)
    return redirect('login')

def address_page(request):

    addresses = Address.objects.filter(user=request.user)

    if request.method == "POST":
        form = AddressForm(request.POST)

        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect("address_page")
    else:
        form = AddressForm()

    return render(request, "address.html", {
        "form": form,
        "addresses": addresses
    })

def delete_address(request, id):
    addr = get_object_or_404(Address, id=id, user=request.user)
    addr.delete()
    return redirect('address_page')