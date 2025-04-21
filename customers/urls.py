from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_customer, name='register_customer'),
    path('enter_name/<int:table_id>/', views.enter_name, name='enter_name'),
    path('', views.customer_home, name='customer_home'),
] 