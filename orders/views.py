from django.shortcuts import render, redirect
from .models import Order, OrderItem, Notification
from menu.models import MenuItem
from tables.models import Table
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth, TruncDay, ExtractMonth, ExtractYear
import datetime
import calendar
import json

def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

def confirm_order(request):
    if request.method == 'POST':
        # Process the order
        # Lấy thông tin từ session
        cart = request.session.get('cart', {})
        customer_name = request.session.get('customer_name', 'Guest')
        table_id = request.session.get('table_id', 1)
        
        # Debug thông tin
        print(f"CONFIRM_ORDER: session table_id={table_id}, customer_name={customer_name}")
        
        # Tạo đơn hàng mới
        try:
            table = Table.objects.get(id=table_id)
            order = Order.objects.create(
                customer_name=customer_name,
                table=table,
                status='pending'
            )
            
            # Cập nhật trạng thái bàn thành 'occupied' (đang sử dụng)
            if table.status != 'occupied':
                table.status = 'occupied'
                table.save()
                print(f"Đã cập nhật trạng thái bàn {table.number} thành 'occupied'")
            
            # Tạo chi tiết đơn hàng
            total_amount = 0
            items_text = ""
            
            for item_id, quantity in cart.items():
                try:
                    menu_item = MenuItem.objects.get(id=item_id)
                    item_total = menu_item.price * quantity
                    total_amount += item_total
                    
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=quantity,
                        price=menu_item.price
                    )
                    
                    # Thêm thông tin món vào text
                    items_text += f"{quantity}x {menu_item.name} ({item_total:,} đ), "
                    
                except MenuItem.DoesNotExist:
                    pass
            
            # Tạo thông báo cho admin
            current_time = timezone.now().strftime("%H:%M:%S")
            notification_message = f"Đơn hàng mới từ {customer_name} tại Bàn {table.number} lúc {current_time}. Tổng tiền: {total_amount:,} đ. Các món: {items_text[:-2]}"
            
            Notification.objects.create(
                order=order,
                message=notification_message
            )
            
            # Xóa giỏ hàng sau khi đặt hàng thành công
            request.session['cart'] = {}
            request.session.modified = True
            
            # Chuyển hướng đến trang hoàn thành đơn hàng
            return redirect('order_complete')
        
        except Table.DoesNotExist:
            messages.error(request, "Bàn không tồn tại, vui lòng chọn bàn khác")
            return redirect('table_list')
    
    # Get cart items
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('menu_list')
    
    # Get customer and table info
    customer_name = request.session.get('customer_name', 'Guest')
    table_id = request.session.get('table_id', 1)
    
    # Debug thông tin
    print(f"CONFIRM_ORDER (GET): session table_id={table_id}, customer_name={customer_name}")
    
    # Lấy thông tin bàn từ table_id
    try:
        table = Table.objects.get(id=table_id)
        table_number = table.number
    except Table.DoesNotExist:
        table_number = "Không xác định"
    
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
        'table_number': table_number,
        'table_id': table_id
    }
    
    return render(request, 'orders/confirm_order.html', context)

def order_complete(request):
    # Lấy thông tin từ session
    customer_name = request.session.get('customer_name', 'Guest')
    table_id = request.session.get('table_id', 1)
    
    # Debug thông tin
    print(f"ORDER_COMPLETE: session table_id={table_id}, customer_name={customer_name}")
    
    # Lấy thông tin bàn từ table_id
    try:
        table = Table.objects.get(id=table_id)
        table_number = table.number
    except Table.DoesNotExist:
        table_number = "Không xác định"
    
    # Lấy thông báo gần nhất
    notifications = Notification.objects.order_by('-created_at')[:5]
    
    # Đảm bảo table_number là kiểu dữ liệu string
    table_number = str(table_number)
    
    context = {
        'customer_name': customer_name,
        'table_number': table_number,
        'notifications': notifications
    }
    
    # Debug context
    print(f"ORDER_COMPLETE context: table_number={table_number}")
    
    # Thử sử dụng template cũ với định dạng mới
    return render(request, 'orders/order_complete.html', context)

def monthly_revenue_report(request):
    """
    Hiển thị báo cáo doanh thu theo tháng.
    Cho phép chọn tháng/năm và hiển thị tổng bill trong tháng đó.
    """
    # Lấy tháng và năm hiện tại làm mặc định
    now = timezone.now()
    year = request.GET.get('year', now.year)
    month = request.GET.get('month', now.month)
    
    try:
        year = int(year)
        month = int(month)
        # Kiểm tra giá trị hợp lệ
        if month < 1 or month > 12 or year < 2000 or year > 9999:
            raise ValueError
    except ValueError:
        year = now.year
        month = now.month
    
    # Lấy danh sách tất cả các năm có đơn hàng để hiển thị trong dropdown
    all_years = Order.objects.dates('created_at', 'year').values_list('created_at__year', flat=True).distinct()
    if not all_years:
        all_years = [now.year]
    
    # Lọc đơn hàng theo tháng và năm đã chọn
    orders = Order.objects.filter(
        created_at__year=year,
        created_at__month=month,
        status='completed'  # Chỉ tính các đơn hàng đã hoàn thành
    )
    
    # Tính tổng doanh thu theo tháng
    total_revenue = sum(order.get_total() for order in orders)
    total_orders = orders.count()
    
    # Phân tích theo ngày trong tháng
    daily_data = orders.annotate(day=TruncDay('created_at')).values('day').annotate(
        daily_total=Sum(F('orderitem__quantity') * F('orderitem__price')),
        order_count=Count('id')
    ).order_by('day')
    
    # Tạo danh sách các ngày trong tháng và doanh thu tương ứng
    days_in_month = []
    revenue_by_day = []
    orders_by_day = []
    
    for data in daily_data:
        days_in_month.append(data['day'].day)
        revenue_by_day.append(float(data['daily_total'] or 0))
        orders_by_day.append(data['order_count'])
    
    # Phân tích theo loại món (để hiển thị biểu đồ tròn)
    category_data = OrderItem.objects.filter(
        order__created_at__year=year,
        order__created_at__month=month,
        order__status='completed'
    ).values('menu_item__category').annotate(
        category_total=Sum(F('quantity') * F('price'))
    ).order_by('-category_total')
    
    # Lấy dữ liệu doanh thu 12 tháng trong năm hiện tại để so sánh
    monthly_comparison = get_monthly_revenue_comparison(year)
    
    # Lấy dữ liệu doanh thu theo năm để so sánh
    yearly_comparison = get_yearly_revenue_comparison()
    
    # Danh sách tháng để hiển thị dropdown
    months = [
        (1, 'Tháng 1'), (2, 'Tháng 2'), (3, 'Tháng 3'),
        (4, 'Tháng 4'), (5, 'Tháng 5'), (6, 'Tháng 6'),
        (7, 'Tháng 7'), (8, 'Tháng 8'), (9, 'Tháng 9'),
        (10, 'Tháng 10'), (11, 'Tháng 11'), (12, 'Tháng 12')
    ]
    
    context = {
        'year': year,
        'month': month,
        'all_years': all_years,
        'months': months,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'orders': orders,
        'daily_data': daily_data,
        'days_in_month': days_in_month,
        'revenue_by_day': revenue_by_day,
        'orders_by_day': orders_by_day,
        'category_data': category_data,
        'monthly_comparison': json.dumps(monthly_comparison),
        'yearly_comparison': json.dumps(yearly_comparison),
    }
    
    return render(request, 'orders/monthly_revenue_report.html', context)

def get_monthly_revenue_comparison(year):
    """
    Lấy dữ liệu doanh thu hàng tháng trong một năm để so sánh
    """
    months_data = Order.objects.filter(
        created_at__year=year,
        status='completed'
    ).annotate(
        month=ExtractMonth('created_at')
    ).values('month').annotate(
        total=Sum(F('orderitem__quantity') * F('orderitem__price')),
        order_count=Count('id')
    ).order_by('month')
    
    # Tạo mảng dữ liệu cho tất cả 12 tháng
    monthly_revenue = [0] * 12
    monthly_orders = [0] * 12
    
    for data in months_data:
        month_idx = data['month'] - 1  # Chuyển từ 1-12 sang 0-11 cho mảng
        monthly_revenue[month_idx] = float(data['total'] or 0)
        monthly_orders[month_idx] = data['order_count']
    
    # Danh sách tên các tháng
    month_names = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
                   'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12']
    
    return {
        'labels': month_names,
        'revenues': monthly_revenue,
        'orders': monthly_orders
    }

def get_yearly_revenue_comparison():
    """
    Lấy dữ liệu doanh thu theo năm để so sánh
    """
    years_data = Order.objects.filter(
        status='completed'
    ).annotate(
        year=ExtractYear('created_at')
    ).values('year').annotate(
        total=Sum(F('orderitem__quantity') * F('orderitem__price')),
        order_count=Count('id')
    ).order_by('year')
    
    years = []
    yearly_revenue = []
    yearly_orders = []
    
    for data in years_data:
        years.append(int(data['year']))
        yearly_revenue.append(float(data['total'] or 0))
        yearly_orders.append(data['order_count'])
    
    return {
        'years': years,
        'revenues': yearly_revenue,
        'orders': yearly_orders
    }

def get_current_month_revenue():
    """
    Lấy doanh thu tháng hiện tại cho dashboard admin
    """
    now = timezone.now()
    current_month = now.month
    current_year = now.year
    
    # Lọc đơn hàng theo tháng và năm hiện tại
    orders = Order.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month,
        status='completed'  # Chỉ tính các đơn hàng đã hoàn thành
    )
    
    # Tính tổng doanh thu tháng hiện tại
    total_revenue = sum(order.get_total() for order in orders)
    total_orders = orders.count()
    
    # Lấy tổng số ngày trong tháng
    _, num_days = calendar.monthrange(current_year, current_month)
    
    # Tính doanh thu trung bình mỗi ngày
    if now.day > 0:  # Tránh chia cho 0
        avg_daily_revenue = total_revenue / now.day
    else:
        avg_daily_revenue = 0
    
    # Dự báo doanh thu cả tháng dựa trên trung bình hiện tại
    projected_revenue = avg_daily_revenue * num_days
    
    return {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_daily_revenue': avg_daily_revenue,
        'projected_revenue': projected_revenue,
        'current_month': current_month,
        'current_year': current_year,
        'days_passed': now.day,
        'total_days': num_days
    }