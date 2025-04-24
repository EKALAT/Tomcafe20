#!/usr/bin/env python
"""
Script cập nhật tự động trạng thái bàn và đơn hàng
---------------------------------------------------
Chạy script này định kỳ (ví dụ: 5 phút/lần) để đảm bảo trạng thái bàn luôn đồng bộ với các đơn hàng.

Hướng dẫn sử dụng:
1. Chạy trực tiếp: python auto_update.py
2. Cài đặt cron job (Linux) hoặc Task Scheduler (Windows) để chạy định kỳ

Trong Windows Task Scheduler, bạn có thể thiết lập như sau:
- Program/script: path/to/python.exe
- Arguments: path/to/auto_update.py
- Start in: path/to/project/folder

Chi tiết được ghi vào file auto_update.log trong thư mục hiện tại.
"""

import os
import sys
import django
import datetime
import logging

# Thiết lập logging
logging.basicConfig(
    filename='auto_update.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tomcafe_20.settings')
django.setup()

from tables.models import Table
from orders.models import Order

def update_tables_status():
    """Cập nhật trạng thái bàn dựa trên đơn hàng hiện tại"""
    logging.info("Bắt đầu cập nhật trạng thái bàn...")
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
        logging.info(f"Đã cập nhật {len(tables_updated)} bàn:")
        for update in tables_updated:
            logging.info(f"  - {update}")
    else:
        logging.info("Tất cả bàn đã được đồng bộ với trạng thái đơn hàng.")

def check_old_pending_orders():
    """Kiểm tra và đánh dấu đơn hàng cũ chưa hoàn thành"""
    # Đánh dấu các đơn hàng 'pending' quá 3 ngày là 'cancelled'
    three_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)
    old_pending_orders = Order.objects.filter(
        status='pending',
        created_at__lt=three_days_ago
    )
    
    if old_pending_orders.exists():
        count = old_pending_orders.count()
        logging.warning(f"Phát hiện {count} đơn hàng 'pending' quá 3 ngày. Đánh dấu là 'cancelled'.")
        
        for order in old_pending_orders:
            order.status = 'cancelled'
            order.save()
            
            # Cập nhật trạng thái bàn nếu cần
            if order.table:
                # Kiểm tra xem có đơn hàng nào khác đang hoạt động trên bàn này không
                active_orders = Order.objects.filter(
                    table=order.table, 
                    status__in=['pending', 'preparing']
                ).exclude(id=order.id).count()
                
                if active_orders == 0:
                    order.table.status = 'available'
                    order.table.save()
                    logging.info(f"Bàn #{order.table.number} đã được đánh dấu là 'trống' vì đơn hàng cũ đã hủy.")

def run_update():
    """Chạy tất cả các cập nhật tự động"""
    try:
        logging.info("===== Bắt đầu cập nhật tự động =====")
        update_tables_status()
        check_old_pending_orders()
        logging.info("===== Hoàn thành cập nhật tự động =====")
    except Exception as e:
        logging.error(f"LỖI: {str(e)}")

if __name__ == "__main__":
    run_update()