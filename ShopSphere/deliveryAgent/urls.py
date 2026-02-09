from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # All three URL names now point to the same view function
    path('', views.agent_portal, name='agentPortal'),
    path('login/', views.agent_portal, name='agentLogin'),
    path('register/', views.agent_portal, name='agentRegister'),
    
    # Logout still uses the built-in Django view
    path('logout/', LogoutView.as_view(next_page='agentPortal'), name='logout'),
]