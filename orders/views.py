from django.shortcuts import render, redirect
from .models import Order, OrderItem
from menu.models import MenuItem

def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

def confirm_order(request):
    if request.method == 'POST':
        # Process the order
        # This is a simplified version
        return redirect('order_complete')
    
    # Get cart items
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('menu_list')
    
    # Get customer and table info
    customer_name = request.session.get('customer_name', 'Guest')
    table_number = request.session.get('table_number', 1)
    
    # Prepare cart items for display
    cart_items = []
    total = 0
    
    for item_id, quantity in cart.items():
        try:
            menu_item = MenuItem.objects.get(id=item_id)
            item_total = menu_item.price * quantity
            total += item_total
            cart_items.append({
                'id': item_id,
                'name': menu_item.name,
                'price': menu_item.price,
                'quantity': quantity,
                'total': item_total
            })
        except MenuItem.DoesNotExist:
            pass
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'customer_name': customer_name,
        'table_number': table_number
    }
    
    return render(request, 'orders/confirm_order.html', context)