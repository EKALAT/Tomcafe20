from django.shortcuts import render, redirect
from .models import MenuItem
from django.conf import settings
import os
from django.http import HttpResponse
from tables.models import Table


def menu_list(request):
    # Lấy table_id từ query param hoặc session
    table_id_param = request.GET.get('table')
    
    # Nếu có table_id trong param, cập nhật session
    if table_id_param:
        request.session['table_id'] = table_id_param
    
    # Lấy table_id từ session
    table_id = request.session.get('table_id')
    
    # Lấy thông tin bàn từ table_id
    try:
        table = Table.objects.get(id=table_id)
        table_number = table.number
    except Table.DoesNotExist:
        table_number = "Không xác định"
    except:
        table_number = "Không xác định"
    
    # Debug thông tin
    print(f"MENU_LIST: session table_id={table_id}, table_number={table_number}")
    
    # Lọc theo category nếu có
    category = request.GET.get('category')
    
    # Lọc menu items
    if category:
        if hasattr(MenuItem, 'available'):
            menu_items = MenuItem.objects.filter(category=category, available=True)
        else:
            menu_items = MenuItem.objects.filter(category=category)
    else:
        if hasattr(MenuItem, 'available'):
            menu_items = MenuItem.objects.filter(available=True)
        else:
            menu_items = MenuItem.objects.all()
    
    # Lấy tất cả categories để hiển thị filter
    categories = MenuItem.objects.values_list('category', flat=True).distinct()
    
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'category': category,
        'table_id': table_id,
        'table_number': table_number,
        'media_url': settings.MEDIA_URL,
    }
    
    # Use the standalone template for the regular menu view
    return render(request, 'menu/menu_standalone.html', context)


def menu_standalone(request):
    # Enhanced debugging
    print("\n=== MENU STANDALONE VIEW ===")
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    
    category = request.GET.get('category')
    print(f"Requested category: {category}")
    
    # Get all menu items regardless of availability first (for debugging)
    all_items = MenuItem.objects.all()
    print(f"Total items in database: {all_items.count()}")
    
    for item in all_items:
        print(f"Item: {item.name}, Category: {item.category}, Available: {getattr(item, 'available', True)}")
        if item.image:
            print(f"  Image: {item.image.url}")
        else:
            print("  No image available")
    
    # Now filter menu items properly
    if category:
        # Check if 'available' field exists before filtering by it
        if hasattr(MenuItem, 'available'):
            menu_items = MenuItem.objects.filter(category=category, available=True)
        else:
            menu_items = MenuItem.objects.filter(category=category)
    else:
        # Check if 'available' field exists before filtering by it
        if hasattr(MenuItem, 'available'):
            menu_items = MenuItem.objects.filter(available=True)
        else:
            menu_items = MenuItem.objects.all()
    
    print(f"Filtered menu items count: {menu_items.count()}")
    
    # Get all unique categories for the filter buttons
    categories = MenuItem.objects.values_list('category', flat=True).distinct()
    print(f"Available categories: {list(categories)}")
    
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'category': category,
        'debug_mode': settings.DEBUG,
        'media_url': settings.MEDIA_URL,
    }
    
    return render(request, 'menu/menu_standalone.html', context)


def add_to_cart(request, item_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        cart[str(item_id)] = cart.get(str(item_id), 0) + quantity
        request.session['cart'] = cart
    return redirect('menu_list')


def test_menu_items(request):
    """A simple view to test if menu items can be retrieved"""
    menu_items = MenuItem.objects.all()
    response_text = "Menu Items:<br>"
    for item in menu_items:
        response_text += f"- {item.name} ({item.category}): {item.price} บาท<br>"
        if item.image:
            response_text += f"  Image: {item.image.url}<br>"
        else:
            response_text += "  No image<br>"
    
    return HttpResponse(response_text)