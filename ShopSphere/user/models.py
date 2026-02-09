from django.db import models
from django.contrib.auth.models import AbstractUser

class AuthUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    ROLE_CHOICES = [
        ('customer', 'Customer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return f"{self.email} - {self.role}"


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} Cart"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def total_price(self):
        return self.product.price * self.quantity

class Order(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    payment_mode = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    item_names = models.TextField(default="") # Stores summary/list of item names
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_name} in Order {self.order.id}"
    
class Address(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)  # ← use AuthUser
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    pincode = models.CharField(max_length=6)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.city}"