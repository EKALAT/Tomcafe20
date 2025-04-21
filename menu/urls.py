from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu_list, name='menu_list'),
    path('standalone/', views.menu_standalone, name='menu_standalone'),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('test-menu-items/', views.test_menu_items, name='test_menu_items'),
]