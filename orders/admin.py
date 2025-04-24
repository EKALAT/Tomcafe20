from django.contrib import admin
from .models import Order, OrderItem, Notification
from django.urls import path
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['menu_item', 'quantity', 'price']
    can_delete = False

class NotificationInline(admin.TabularInline):
    model = Notification
    extra = 0
    readonly_fields = ['message', 'created_at']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'table_number', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name', 'table__number']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline, NotificationInline]
    
    def table_number(self, obj):
        return obj.table.number
    
    def total_amount(self, obj):
        return f"{obj.get_total():,} đ"
    
    table_number.short_description = "Bàn số"
    total_amount.short_description = "Tổng tiền"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('monthly-revenue/', self.admin_site.admin_view(self.monthly_revenue_view), name='monthly_revenue_admin'),
        ]
        return custom_urls + urls
    
    def monthly_revenue_view(self, request):
        """Chuyển hướng đến trang báo cáo doanh thu theo tháng"""
        return redirect('monthly_revenue_report')
    
    def changelist_view(self, request, extra_context=None):
        """Thêm nút báo cáo doanh thu vào trang danh sách đơn hàng"""
        extra_context = extra_context or {}
        extra_context['monthly_revenue_button'] = format_html(
            '<a href="{}" class="button" style="margin-right: 5px; background-color: #28a745; color: #fff;">'
            'Xem báo cáo doanh thu tháng</a>',
            reverse('admin:monthly_revenue_admin')
        )
        return super().changelist_view(request, extra_context)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_order_info', 'message_truncated', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['message', 'order__customer_name']
    readonly_fields = ['order', 'message', 'created_at']
    list_editable = ['status']
    list_per_page = 20
    
    def get_order_info(self, obj):
        return f"#{obj.order.id} - {obj.order.customer_name} - Bàn {obj.order.table.number}"
    
    def message_truncated(self, obj):
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
    
    get_order_info.short_description = "Đơn hàng"
    message_truncated.short_description = "Nội dung"
