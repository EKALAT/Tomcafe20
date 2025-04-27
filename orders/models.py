from django.db import models

# Create your models here.
from django.db import models
from menu.models import MenuItem
from tables.models import Table

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Chờ xử lý'),
        ('preparing', 'Đang chuẩn bị'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    )
    
    customer_name = models.CharField(max_length=100)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_total(self):
        total = 0
        for item in self.orderitem_set.all():
            total += item.quantity * item.price
        return total
    
    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.customer_name} - Bàn {self.table.number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # Giữ lại trường item để tương thích ngược
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='order_items_legacy', null=True, blank=True)
    # Thêm trường menu_item mới, cho phép null trong quá trình chuyển đổi
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='order_items', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    
    def get_total(self):
        return self.quantity * self.price
    
    def __str__(self):
        if self.menu_item:
            return f"{self.quantity}x {self.menu_item.name}"
        elif self.item:
            return f"{self.quantity}x {self.item.name}"
        else:
            return f"{self.quantity}x [Món không xác định]"

class Notification(models.Model):
    STATUS_CHOICES = (
        ('unread', 'Chưa đọc'),
        ('read', 'Đã đọc'),
    )
    
    NOTIFICATION_TYPES = (
        ('order', 'Đơn hàng'),
        ('system', 'Hệ thống'),
        ('info', 'Thông tin'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unread')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='order')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Thông báo về đơn hàng #{self.order.id}"
    
    class Meta:
        ordering = ['-created_at']
