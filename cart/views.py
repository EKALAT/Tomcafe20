from django.shortcuts import render, redirect
from menu.models import MenuItem


def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    
    for item_id, quantity in cart.items():
        try:
            item = MenuItem.objects.get(id=item_id)
            subtotal = item.price * quantity
            total += subtotal
            cart_items.append({
                'id': item_id,
                'name': item.name,
                'price': item.price,
                'image': item.image,
                'category': item.category,
                'quantity': quantity,
                'total': subtotal
            })
        except MenuItem.DoesNotExist:
            pass
    
    context = {
        'cart_items': cart_items,
        'total_items': len(cart_items),
        'cart_total': total,
        'customer_name': request.session.get('customer_name', 'Guest'),
        'table_number': request.session.get('table_number', '1')
    }
    
    return render(request, 'cart/cart_detail.html', context)


def clear_cart(request):
    request.session['cart'] = {}
    return redirect('view_cart')


def update_cart(request, item_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        cart = request.session.get('cart', {})
        
        if str(item_id) in cart:
            if action == 'increase':
                cart[str(item_id)] += 1
            elif action == 'decrease':
                if cart[str(item_id)] > 1:
                    cart[str(item_id)] -= 1
                else:
                    del cart[str(item_id)]
        
        request.session['cart'] = cart
    
    return redirect('view_cart')


def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if str(item_id) in cart:
            del cart[str(item_id)]
            request.session['cart'] = cart
    
    return redirect('view_cart')