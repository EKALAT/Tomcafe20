import os
import django
from django.contrib import messages

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tomcafe_20.settings')
django.setup()

from tables.models import Table
from orders.models import Order

def check_table_status():
    """Kiểm tra và đồng bộ trạng thái bàn với đơn hàng"""
    print("Bắt đầu kiểm tra trạng thái bàn...")
    tables = Table.objects.all()
    tables_updated = []
    
    for table in tables:
        # Tìm đơn hàng đang hoạt động trên bàn này
        active_orders = Order.objects.filter(
            table=table,
            status__in=['pending', 'preparing']
        ).count()
        
        # Nếu có đơn hàng đang hoạt động nhưng bàn đang trống, cập nhật trạng thái bàn
        if active_orders > 0 and table.status != 'occupied':
            old_status = table.status
            table.status = 'occupied'
            table.save()
            tables_updated.append(f"Bàn #{table.number}: {old_status} -> occupied")
        
        # Nếu không có đơn hàng đang hoạt động nhưng bàn đang có khách, cập nhật trạng thái bàn
        elif active_orders == 0 and table.status == 'occupied':
            table.status = 'available'
            table.save()
            tables_updated.append(f"Bàn #{table.number}: occupied -> available")
    
    if tables_updated:
        print(f"Đã cập nhật {len(tables_updated)} bàn:")
        for update in tables_updated:
            print(f"  - {update}")
    else:
        print("Tất cả bàn đã đồng bộ với trạng thái đơn hàng.")

def update_table_status_for_order(order):
    """Cập nhật trạng thái bàn dựa trên trạng thái đơn hàng"""
    if not order.table:
        return
    
    # Nếu đơn hàng có bàn và không ở trạng thái đã huỷ, cập nhật trạng thái bàn thành 'occupied'
    if order.status != 'cancelled' and order.status != 'completed':
        order.table.status = 'occupied'
        order.table.save()
        print(f"Đã cập nhật bàn #{order.table.number} thành 'đang có khách'.")
    
    # Nếu đơn hàng đã huỷ hoặc hoàn thành, kiểm tra xem bàn có đơn hàng khác không
    elif order.status == 'cancelled' or order.status == 'completed':
        # Kiểm tra xem có đơn hàng nào khác đang hoạt động trên bàn này không
        active_orders = Order.objects.filter(
            table=order.table, 
            status__in=['pending', 'preparing']
        ).exclude(id=order.id).count()
        
        if active_orders == 0:
            order.table.status = 'available'
            order.table.save()
            print(f"Bàn #{order.table.number} đã được đánh dấu là 'trống' vì không còn đơn hàng đang hoạt động.")

if __name__ == "__main__":
    check_table_status()