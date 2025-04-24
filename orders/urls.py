from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('confirm/', views.confirm_order, name='confirm_order'),
    path('complete/', views.order_complete, name='order_complete'),
    path('monthly-revenue/', views.monthly_revenue_report, name='monthly_revenue_report'),
]
