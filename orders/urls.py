from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('confirm/', views.confirm_order, name='confirm_order'),
]
