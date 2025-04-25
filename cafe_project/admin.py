from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.contrib import messages
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import TruncDay, TruncMonth
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe
from django.template.loader import get_template
from django.conf import settings
from django.utils import timezone
from io import BytesIO

import os
import datetime
import calendar
import xlsxwriter
import xhtml2pdf.pisa as pisa

from orders.models import Order, OrderItem
from tables.models import Table
from menu.models import MenuItem
from customers.models import Customer
from django.contrib.auth.models import User

# Thiết kế Admin Site mới
class TomCafeAdminSite(AdminSite):
    """
    Quản lý trang admin của TomCafe
    """
    site_title = _("TomCafe - Quản lý")
    site_header = _("TomCafe - Hệ thống quản lý quán cà phê")
    index_title = _("Chào mừng đến với TomCafe Admin")
    
    # Thêm thông tin thống kê vào dashboard
    def index(self, request, extra_context=None):
        # Đếm số bàn
        from tables.models import Table
        table_count = Table.objects.count()
        available_tables = Table.objects.filter(status='available', is_active=True).count()
        occupied_tables = Table.objects.filter(status='occupied', is_active=True).count()
        unavailable_tables = Table.objects.filter(status='unavailable', is_active=True).count()
        
        # Đếm số món trong menu
        from menu.models import MenuItem
        menu_count = MenuItem.objects.count()
        
        # Đếm số đơn hàng hôm nay
        from orders.models import Order
        today = timezone.now().date()
        order_count = Order.objects.filter(
            created_at__date=today
        ).count()
        
        # Tính toán doanh thu hôm nay - Chỉ từ đơn hàng đã hoàn thành
        today_revenue = 0
        today_completed_orders = Order.objects.filter(
            created_at__date=today,
            status='completed'  # Chỉ tính đơn hàng đã hoàn thành
        )
        
        for order in today_completed_orders:
            for item in order.orderitem_set.all():
                if item.menu_item:
                    today_revenue += item.menu_item.price * item.quantity
                elif item.item:
                    today_revenue += item.item.price * item.quantity
        
        # Tính doanh thu tháng này
        current_month = today.month
        current_year = today.year
        first_day = datetime.date(current_year, current_month, 1)
        last_day = datetime.date(current_year, current_month, calendar.monthrange(current_year, current_month)[1])
        
        month_revenue = 0
        month_completed_orders = Order.objects.filter(
            created_at__date__gte=first_day,
            created_at__date__lte=last_day,
            status='completed'
        )
        
        for order in month_completed_orders:
            for item in order.orderitem_set.all():
                if item.menu_item:
                    month_revenue += item.menu_item.price * item.quantity
                elif item.item:
                    month_revenue += item.item.price * item.quantity
        
        # Đếm số đơn hàng theo trạng thái hôm nay
        completed_today_count = today_completed_orders.count()
        pending_today_count = Order.objects.filter(
            created_at__date=today,
            status='pending'
        ).count()
        preparing_today_count = Order.objects.filter(
            created_at__date=today,
            status='preparing'
        ).count()
        cancelled_today_count = Order.objects.filter(
            created_at__date=today,
            status='cancelled'
        ).count()
        
        # Tình trạng đơn hàng tổng thể
        pending_orders = Order.objects.filter(status='pending').count()
        preparing_orders = Order.objects.filter(status='preparing').count()
        active_orders = pending_orders + preparing_orders
        completed_orders = Order.objects.filter(status='completed').count()
        
        # Tính số đơn chưa hoàn thành và giá trị
        unpaid_orders = Order.objects.filter(status__in=['pending', 'preparing'])
        unpaid_count = unpaid_orders.count()
        unpaid_value = 0
        
        for order in unpaid_orders:
            for item in order.orderitem_set.all():
                if item.menu_item:
                    unpaid_value += item.menu_item.price * item.quantity
                elif item.item:
                    unpaid_value += item.item.price * item.quantity
        
        # Đếm số khách hàng và người dùng
        from customers.models import Customer
        from django.contrib.auth.models import User
        customer_count = Customer.objects.count()
        user_count = User.objects.count()
        
        # Tính giá trị trung bình đơn hàng
        avg_order_value = 0
        if completed_orders > 0:
            all_completed_orders = Order.objects.filter(status='completed')
            total_all_orders_value = 0
            for order in all_completed_orders:
                order_value = 0
                for item in order.orderitem_set.all():
                    if item.menu_item:
                        order_value += item.menu_item.price * item.quantity
                    elif item.item:
                        order_value += item.item.price * item.quantity
                total_all_orders_value += order_value
            avg_order_value = total_all_orders_value / all_completed_orders.count()
        
        # Tìm món phổ biến nhất
        from django.db.models import Count, Sum
        from orders.models import OrderItem
        
        popular_items = {}
        for order in Order.objects.filter(status='completed'):
            for item in order.orderitem_set.all():
                name = None
                if item.menu_item:
                    name = item.menu_item.name
                elif item.item:
                    name = item.item.name
                
                if name:
                    if name in popular_items:
                        popular_items[name] += item.quantity
                    else:
                        popular_items[name] = item.quantity
        
        # Sắp xếp và lấy top 5 món bán chạy nhất
        top_items = sorted(popular_items.items(), key=lambda x: x[1], reverse=True)[:5]
        most_popular_item = top_items[0][0] if top_items else "Chưa có dữ liệu"
        most_popular_count = top_items[0][1] if top_items else 0
        
        # Đồng bộ trạng thái bàn trước khi hiển thị dashboard
        self.check_table_status(request)
        
        # Tạo context bổ sung
        my_context = {
            'table_count': table_count,
            'available_tables': available_tables,
            'occupied_tables': occupied_tables,
            'unavailable_tables': unavailable_tables,
            'menu_count': menu_count,
            'order_count': order_count,
            'active_orders': active_orders,
            'today_revenue': "{:,.0f}".format(today_revenue).replace(',', '.'),
            'month_revenue': "{:,.0f}".format(month_revenue).replace(',', '.'),
            'pending_orders': pending_orders,
            'preparing_orders': preparing_orders,
            'completed_orders': completed_orders,
            'completed_today_count': completed_today_count,
            'pending_today_count': pending_today_count,
            'preparing_today_count': preparing_today_count,
            'cancelled_today_count': cancelled_today_count,
            'customer_count': customer_count,
            'user_count': user_count,
            'avg_order_value': "{:,.0f}".format(avg_order_value).replace(',', '.'),
            'most_popular_item': most_popular_item,
            'most_popular_count': most_popular_count,
            'top_items': top_items,
            'unpaid_count': unpaid_count,
            'unpaid_value': "{:,.0f}".format(unpaid_value).replace(',', '.'),
        }
        
        # Kết hợp với context hiện có
        if extra_context:
            my_context.update(extra_context)
        
        return super().index(request, my_context)

    def check_table_status(self, request):
        """Kiểm tra và đồng bộ trạng thái bàn và đơn hàng
        
        Method này sẽ duyệt qua tất cả các bàn và đảm bảo trạng thái bàn phản ánh đúng
        trạng thái của các đơn hàng liên quan. Cụ thể:
        - Nếu bàn có ít nhất một đơn hàng đang hoạt động (pending hoặc preparing), 
          bàn sẽ được đánh dấu là 'occupied'
        - Nếu bàn không có đơn hàng nào đang hoạt động, bàn sẽ được đánh dấu là 'available'
          (trừ khi bàn được đánh dấu là 'unavailable' do admin cấu hình)
        """
        # Kiểm tra tất cả các bàn
        from tables.models import Table
        from orders.models import Order
        tables = Table.objects.all()
        tables_updated = []
        
        # Đầu tiên, lấy tất cả các đơn hàng đang hoạt động
        active_orders = Order.objects.filter(status__in=['pending', 'preparing'])
        
        # Lấy danh sách bàn đang có khách (từ các đơn đang hoạt động)
        active_table_ids = set(active_orders.values_list('table_id', flat=True))
        
        for table in tables:
            # Bỏ qua bàn bị đánh dấu unavailable (do admin cấu hình)
            if table.status == 'unavailable':
                continue

            # Kiểm tra xem bàn có đơn hàng đang hoạt động hay không
            table_has_active_orders = table.id in active_table_ids
            
            # Trường hợp 1: Bàn có đơn hàng đang hoạt động nhưng đang để trạng thái trống
            if table_has_active_orders and table.status != 'occupied':
                table.status = 'occupied'
                table.save()
                tables_updated.append(f"{table.number} (đang phục vụ)")
            
            # Trường hợp 2: Bàn không có đơn hàng đang hoạt động nhưng đang để trạng thái có khách
            elif not table_has_active_orders and table.status == 'occupied':
                table.status = 'available'
                table.save()
                tables_updated.append(f"{table.number} (trống)")
        
        if tables_updated and request:
            tables_updated_str = ", ".join(tables_updated)
            messages.info(request, f"Đã tự động cập nhật trạng thái của {len(tables_updated)} bàn: {tables_updated_str}")
            
        # Trả về True nếu có bàn nào được cập nhật
        return len(tables_updated) > 0

# Tạo instance của Admin Site mới
tomcafe_admin_site = TomCafeAdminSite(name='tomcafe_admin')

# Đăng ký các model với Admin Site mới
from django.contrib.auth.models import User, Group
from tables.models import Table
from menu.models import MenuItem
from orders.models import Order, OrderItem
from customers.models import Customer

# Tùy chỉnh User Admin
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        ('Thông tin tài khoản', {'fields': ('username', 'password')}),
        ('Thông tin cá nhân', {'fields': ('first_name', 'last_name', 'email')}),
        ('Quyền hạn', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Thông tin quan trọng', {'fields': ('last_login', 'date_joined')}),
    )

tomcafe_admin_site.register(User, CustomUserAdmin)
tomcafe_admin_site.register(Group)

# Đăng ký model Customer
@admin.register(Customer, site=tomcafe_admin_site)
class CustomerAdmin(admin.ModelAdmin):
    """
    Quản lý danh sách khách hàng
    """
    list_display = ('name', 'phone', 'email', 'get_total_orders', 'created_at')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'phone', 'email')
        }),
        (_('Thông tin thêm'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_orders(self, obj):
        return obj.orders.count()
    get_total_orders.short_description = 'Tổng số đơn hàng'

# Đăng ký model Table
@admin.register(Table, site=tomcafe_admin_site)
class TableAdmin(admin.ModelAdmin):
    """
    Quản lý bàn trong quán
    """
    list_display = ('number', 'status', 'capacity')
    list_filter = ('status',)
    search_fields = ('number',)
    ordering = ('number',)
    
    def get_status_display(self, obj):
        status_map = {
            'available': '<span style="color:green; font-weight:bold;">Trống</span>',
            'occupied': '<span style="color:red; font-weight:bold;">Đang sử dụng</span>',
            'reserved': '<span style="color:orange; font-weight:bold;">Đã đặt trước</span>',
            'unavailable': '<span style="color:gray; font-weight:bold;">Không sẵn sàng</span>',
        }
        return mark_safe(status_map.get(obj.status, obj.status))
    get_status_display.short_description = 'Trạng thái'
    
    def make_available(self, request, queryset):
        queryset.update(status='available')
    make_available.short_description = "Đánh dấu bàn trống"
    
    def make_unavailable(self, request, queryset):
        queryset.update(status='unavailable')
    make_unavailable.short_description = "Đánh dấu bàn không sẵn sàng"

# Đăng ký model MenuItem
class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and getattr(value, "url", None):
            image_url = value.url
            output.append(f'<a href="{image_url}" target="_blank">'
                         f'<img src="{image_url}" alt="{name}" width="150" height="150" '
                         f'style="object-fit: cover; border-radius: 8px; border: 1px solid #ddd;"/></a>')
        output.append(super().render(name, value, attrs, renderer))
        return mark_safe(''.join(output))

@admin.register(MenuItem, site=tomcafe_admin_site)
class MenuItemAdmin(admin.ModelAdmin):
    """
    Quản lý menu của quán
    """
    list_display = ('name', 'category', 'price', 'available', 'image_tag')
    list_filter = ('category', 'available')
    search_fields = ('name', 'description')
    readonly_fields = ('image_tag',)
    
    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="80" height="80" style="object-fit: cover; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" />')
        return mark_safe('<span style="color:#999;">Không có hình ảnh</span>')
    image_tag.short_description = 'Hình ảnh'
    image_tag.allow_tags = True
    
    def format_price(self, obj):
        return f"{obj.price:,.0f} đ"
    format_price.short_description = 'Giá'
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'image':
            kwargs.pop("request", None)
            kwargs['widget'] = AdminImageWidget
            return db_field.formfield(**kwargs)
        return super().formfield_for_dbfield(db_field, **kwargs)
    
    fieldsets = (
        ('Thông tin món', {
            'fields': ('name', 'price', 'category', 'available', 'description')
        }),
        ('Hình ảnh', {
            'fields': ('image', 'image_tag'),
            'description': 'Chọn hình ảnh món với độ phân giải tốt (khuyến nghị 500x500 px)'
        }),
    )
    
    def display_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="80" height="80" style="object-fit: cover; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" />')
        return mark_safe('<span style="color:#999;">Không có hình ảnh</span>')
    display_image.short_description = 'Hình ảnh'
    display_image.allow_tags = True

# Đăng ký model Order và OrderItem
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['get_item_name', 'quantity', 'item_price', 'item_total']
    readonly_fields = ['get_item_name', 'item_price', 'item_total']
    can_delete = False
    
    def get_item_name(self, obj):
        if obj.menu_item:
            return mark_safe(f'<div style="display:flex; align-items:center;">'
                           f'<img src="{obj.menu_item.image.url}" width="50" height="50" '
                           f'style="object-fit: cover; border-radius: 8px; margin-right: 10px;" />'
                           f'<strong>{obj.menu_item.name}</strong></div>')
        elif obj.item:
            if obj.item.image:
                return mark_safe(f'<div style="display:flex; align-items:center;">'
                               f'<img src="{obj.item.image.url}" width="50" height="50" '
                               f'style="object-fit: cover; border-radius: 8px; margin-right: 10px;" />'
                               f'<strong>{obj.item.name}</strong></div>')
            return obj.item.name
        return 'Món không xác định'
    get_item_name.short_description = "Tên món"
    
    def item_price(self, obj):
        price = 0
        if obj.menu_item:
            price = obj.menu_item.price
        elif obj.item:
            price = obj.item.price
        return f"{price:,.0f} đ"
    item_price.short_description = "Giá đơn vị"
    
    def item_total(self, obj):
        price = 0
        if obj.menu_item:
            price = obj.menu_item.price
        elif obj.item:
            price = obj.item.price
        return f"{price * obj.quantity:,.0f} đ"
    item_total.short_description = "Thành tiền"

@admin.register(Order, site=tomcafe_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'table', 'formatted_created_at', 'get_status_display', 'order_total', 'view_items', 'generate_invoice')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'table__number')
    readonly_fields = ('created_at', 'updated_at', 'order_summary', 'invoice_pdf')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    actions = ['mark_as_completed', 'mark_as_pending', 'mark_as_preparing', 'mark_as_cancelled', 'generate_invoices']
    change_list_template = 'admin/orders/order/change_list.html'
    
    fieldsets = (
        ('Thông tin đơn hàng', {
            'fields': (
                'customer_name', 'table', 'status',
                'created_at', 'updated_at'
            )
        }),
        ('Thông tin chi tiết', {
            'fields': ('order_summary',),
            'classes': ('collapse',),
        }),
        ('Hóa đơn PDF', {
            'fields': ('invoice_pdf',),
            'classes': ('collapse',),
        })
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('order/invoice/<int:pk>/', self.admin_site.admin_view(self.generate_invoice_pdf), name='order_invoice'),
            path('export-daily-excel/', self.admin_site.admin_view(self.export_daily_report_excel), name='export_daily_excel'),
            path('export-monthly-excel-report/', self.admin_site.admin_view(self.export_monthly_report_excel), name='export_monthly_excel'),
        ]
        return custom_urls + urls
    
    def get_status_display(self, obj):
        status_map = {
            'pending': '<span style="color:white; font-weight:bold; background-color:orange; padding:5px 10px; border-radius:5px;">Chờ xử lý</span>',
            'preparing': '<span style="color:white; font-weight:bold; background-color:blue; padding:5px 10px; border-radius:5px;">Đang chuẩn bị</span>',
            'completed': '<span style="color:white; font-weight:bold; background-color:green; padding:5px 10px; border-radius:5px;">Hoàn thành</span>',
            'cancelled': '<span style="color:white; font-weight:bold; background-color:red; padding:5px 10px; border-radius:5px;">Đã hủy</span>',
        }
        return mark_safe(status_map.get(obj.status, obj.status))
    get_status_display.short_description = 'Trạng thái'
    
    def order_total(self, obj):
        total = 0
        for item in obj.orderitem_set.all():
            if item.menu_item:
                total += item.menu_item.price * item.quantity
            elif item.item:
                total += item.item.price * item.quantity
        return f"{total:,.0f} đ"
    order_total.short_description = 'Tổng tiền'
    
    def view_items(self, obj):
        items = obj.orderitem_set.all()
        count = items.count()
        return mark_safe(f'<a href="{obj.id}/change/" class="button" style="background-color:#007bff; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;">'
                        f'Xem {count} món</a>')
    view_items.short_description = 'Chi tiết'
    
    def generate_invoice(self, obj):
        if obj.status == 'completed':
            return mark_safe(f'<a href="{reverse("admin:order_invoice", args=[obj.id])}" target="_blank" class="button" style="background-color:#28a745; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;">'
                           f'<i class="fas fa-file-pdf"></i> Xuất PDF</a>')
        return '-'
    generate_invoice.short_description = 'Hóa đơn'
    
    def invoice_pdf(self, obj):
        if obj.status == 'completed':
            return mark_safe(f'<a href="{reverse("admin:order_invoice", args=[obj.id])}" target="_blank" class="button" style="background-color:#28a745; color:white; padding:8px 15px; border-radius:5px; text-decoration:none; display: inline-block; margin-top: 10px;">'
                           f'<i class="fas fa-file-pdf"></i> Xuất hóa đơn PDF</a>')
        return mark_safe('<p>Đơn hàng phải được đánh dấu hoàn thành trước khi xuất hóa đơn</p>')
    invoice_pdf.short_description = 'Xuất hóa đơn'
    
    def order_summary(self, obj):
        items = obj.orderitem_set.all()
        if not items:
            return mark_safe('<p>Không có món nào trong đơn hàng này</p>')
        
        html = '<div style="margin-top:10px;">'
        html += '<h3 style="margin-bottom:10px;">Các món trong đơn hàng:</h3>'
        html += '<table style="width:100%; border-collapse:collapse; margin-bottom:20px;">'
        html += '<thead><tr style="background-color:#f5f5f5;">'
        html += '<th style="padding:10px; text-align:left; border:1px solid #ddd;">Món</th>'
        html += '<th style="padding:10px; text-align:center; border:1px solid #ddd;">Số lượng</th>'
        html += '<th style="padding:10px; text-align:right; border:1px solid #ddd;">Đơn giá</th>'
        html += '<th style="padding:10px; text-align:right; border:1px solid #ddd;">Thành tiền</th>'
        html += '</tr></thead><tbody>'
        
        total = 0
        for item in items:
            name = 'Món không xác định'
            price = 0
            
            if item.menu_item:
                name = item.menu_item.name
                price = item.menu_item.price
            elif item.item:
                name = item.item.name
                price = item.item.price
                
            subtotal = price * item.quantity
            total += subtotal
            
            html += f'<tr style="border-bottom:1px solid #ddd;">'
            html += f'<td style="padding:10px; text-align:left; border:1px solid #ddd;"><strong>{name}</strong></td>'
            html += f'<td style="padding:10px; text-align:center; border:1px solid #ddd;">{item.quantity}</td>'
            html += f'<td style="padding:10px; text-align:right; border:1px solid #ddd;">{price:,.0f} đ</td>'
            html += f'<td style="padding:10px; text-align:right; border:1px solid #ddd;">{subtotal:,.0f} đ</td>'
            html += '</tr>'
            
        html += '</tbody>'
        html += f'<tfoot><tr>'
        html += f'<td colspan="3" style="padding:10px; text-align:right; border:1px solid #ddd;"><strong>Tổng cộng:</strong></td>'
        html += f'<td style="padding:10px; text-align:right; border:1px solid #ddd; background-color:#f9f9f9;"><strong>{total:,.0f} đ</strong></td>'
        html += '</tr></tfoot>'
        html += '</table>'
        
        # Order creation date-time in local timezone
        local_datetime = timezone.localtime(obj.created_at)
        formatted_datetime = local_datetime.strftime("%d/%m/%Y %H:%M")
        
        html += f'<p><strong>Ngày tạo đơn:</strong> {formatted_datetime}</p>'
        
        # Thêm nút thay đổi trạng thái
        html += '<div style="display:flex; gap:10px; margin-top:20px;">'
        
        if obj.status != 'pending':
            html += f'<a href="/admin/orders/order/{obj.id}/change/?_changeto=pending" class="button" style="padding:8px 15px; background-color:orange; color:white; text-decoration:none; border-radius:5px;">Đánh dấu chờ xử lý</a>'
        
        if obj.status != 'preparing':
            html += f'<a href="/admin/orders/order/{obj.id}/change/?_changeto=preparing" class="button" style="padding:8px 15px; background-color:blue; color:white; text-decoration:none; border-radius:5px;">Đánh dấu đang chuẩn bị</a>'
        
        if obj.status != 'completed':
            html += f'<a href="/admin/orders/order/{obj.id}/change/?_changeto=completed" class="button" style="padding:8px 15px; background-color:green; color:white; text-decoration:none; border-radius:5px;">Đánh dấu hoàn thành</a>'
        
        if obj.status != 'cancelled':
            html += f'<a href="/admin/orders/order/{obj.id}/change/?_changeto=cancelled" class="button" style="padding:8px 15px; background-color:red; color:white; text-decoration:none; border-radius:5px;">Đánh dấu đã hủy</a>'
        
        html += '</div>'
        html += '</div>'
        
        return mark_safe(html)
    order_summary.short_description = 'Chi tiết đơn hàng'
    
    def mark_as_completed(self, request, queryset):
        """Đánh dấu các đơn hàng đã chọn là 'hoàn thành' và cập nhật trạng thái bàn nếu cần"""
        completed_count = 0
        order_ids = []
        tables_affected = set()
        
        for order in queryset:
            # Chỉ cập nhật đơn hàng chưa hoàn thành
            if order.status != 'completed':
                old_status = order.status
                order.status = 'completed'
                order.save()
                completed_count += 1
                
            # Luôn thêm ID của đơn hàng vào danh sách để báo cáo
            order_ids.append(str(order.id))
            
            # Lưu lại bàn bị ảnh hưởng để cập nhật sau
            if order.table:
                tables_affected.add(order.table.id)
        
        # Thông báo về đơn hàng đã cập nhật
        if completed_count > 0:
            messages.success(request, f"Đã đánh dấu {completed_count} đơn hàng (#{', #'.join(order_ids)}) là hoàn thành.")
            
            # Kiểm tra và cập nhật trạng thái tất cả các bàn sau khi hoàn thành đơn hàng
            admin_site = self.admin_site
            tables_updated = False
            if hasattr(admin_site, 'check_table_status'):
                tables_updated = admin_site.check_table_status(request)
            
            if not tables_updated:
                messages.info(request, "Không có bàn nào cần thay đổi trạng thái.")
        else:
            messages.info(request, "Không có đơn hàng nào được cập nhật trạng thái.")
    mark_as_completed.short_description = "Đánh dấu hoàn thành"
    
    def mark_as_pending(self, request, queryset):
        """Đánh dấu các đơn hàng đã chọn là 'chờ xử lý' và cập nhật trạng thái bàn"""
        updated_count = 0
        order_ids = []
        tables_affected = set()
        
        for order in queryset:
            # Chỉ cập nhật đơn hàng chưa ở trạng thái chờ xử lý
            if order.status != 'pending':
                old_status = order.status
                order.status = 'pending'
                order.save()
                updated_count += 1
                
            # Luôn thêm ID của đơn hàng vào danh sách để báo cáo
            order_ids.append(str(order.id))
            
            # Lưu lại bàn bị ảnh hưởng để cập nhật sau
            if order.table:
                tables_affected.add(order.table.id)
        
        # Thông báo về đơn hàng đã cập nhật
        if updated_count > 0:
            messages.success(request, f"Đã đánh dấu {updated_count} đơn hàng (#{', #'.join(order_ids)}) là chờ xử lý.")
            
            # Kiểm tra và cập nhật trạng thái tất cả các bàn
            admin_site = self.admin_site
            tables_updated = False
            if hasattr(admin_site, 'check_table_status'):
                tables_updated = admin_site.check_table_status(request)
            
            if not tables_updated:
                messages.info(request, "Không có bàn nào cần thay đổi trạng thái.")
        else:
            messages.info(request, "Không có đơn hàng nào được cập nhật trạng thái.")
    mark_as_pending.short_description = "Đánh dấu chờ xử lý"
    
    def mark_as_preparing(self, request, queryset):
        """Đánh dấu các đơn hàng đã chọn là 'đang chuẩn bị' và cập nhật trạng thái bàn"""
        updated_count = 0
        order_ids = []
        tables_affected = set()
        
        for order in queryset:
            # Chỉ cập nhật đơn hàng chưa ở trạng thái đang chuẩn bị
            if order.status != 'preparing':
                old_status = order.status
                order.status = 'preparing'
                order.save()
                updated_count += 1
                
            # Luôn thêm ID của đơn hàng vào danh sách để báo cáo
            order_ids.append(str(order.id))
            
            # Lưu lại bàn bị ảnh hưởng để cập nhật sau
            if order.table:
                tables_affected.add(order.table.id)
        
        # Thông báo về đơn hàng đã cập nhật
        if updated_count > 0:
            messages.success(request, f"Đã đánh dấu {updated_count} đơn hàng (#{', #'.join(order_ids)}) là đang chuẩn bị.")
            
            # Kiểm tra và cập nhật trạng thái tất cả các bàn
            admin_site = self.admin_site
            tables_updated = False
            if hasattr(admin_site, 'check_table_status'):
                tables_updated = admin_site.check_table_status(request)
            
            if not tables_updated:
                messages.info(request, "Không có bàn nào cần thay đổi trạng thái.")
        else:
            messages.info(request, "Không có đơn hàng nào được cập nhật trạng thái.")
    mark_as_preparing.short_description = "Đánh dấu đang chuẩn bị"
    
    def mark_as_cancelled(self, request, queryset):
        """Đánh dấu các đơn hàng đã chọn là 'đã hủy' và cập nhật trạng thái bàn nếu cần"""
        updated_count = 0
        order_ids = []
        tables_affected = set()
        
        for order in queryset:
            # Chỉ cập nhật đơn hàng chưa ở trạng thái đã hủy
            if order.status != 'cancelled':
                old_status = order.status
                order.status = 'cancelled'
                order.save()
                updated_count += 1
                
            # Luôn thêm ID của đơn hàng vào danh sách để báo cáo
            order_ids.append(str(order.id))
            
            # Lưu lại bàn bị ảnh hưởng để cập nhật sau
            if order.table:
                tables_affected.add(order.table.id)
        
        # Thông báo về đơn hàng đã cập nhật
        if updated_count > 0:
            messages.success(request, f"Đã đánh dấu {updated_count} đơn hàng (#{', #'.join(order_ids)}) là đã hủy.")
            
            # Kiểm tra và cập nhật trạng thái tất cả các bàn
            admin_site = self.admin_site
            tables_updated = False
            if hasattr(admin_site, 'check_table_status'):
                tables_updated = admin_site.check_table_status(request)
            
            if not tables_updated:
                messages.info(request, "Không có bàn nào cần thay đổi trạng thái.")
        else:
            messages.info(request, "Không có đơn hàng nào được cập nhật trạng thái.")
    mark_as_cancelled.short_description = "Đánh dấu đã hủy"
    
    def export_daily_report_excel(self, request):
        """Xuất báo cáo doanh thu theo ngày ra file Excel"""
        # Kiểm tra và cập nhật trạng thái bàn
        # Use the check_table_status method from the admin_site instance (tomcafe_admin_site)
        admin_site = self.admin_site
        if hasattr(admin_site, 'check_table_status'):
            admin_site.check_table_status(request)
        
        # Lấy ngày từ request, nếu không có thì dùng ngày hiện tại
        selected_date_str = request.GET.get('date')
        if selected_date_str:
            try:
                selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = timezone.localdate()
        else:
            selected_date = timezone.localdate()
        
        # Lấy tất cả đơn hàng trong ngày
        start_of_day = timezone.make_aware(datetime.datetime.combine(selected_date, datetime.time.min))
        end_of_day = timezone.make_aware(datetime.datetime.combine(selected_date, datetime.time.max))
        orders = Order.objects.filter(created_at__range=(start_of_day, end_of_day))
        
        # Tạo BytesIO object để lưu file Excel
        output = BytesIO()
        
        # Tạo workbook mới với xlsxwriter
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(f'Doanh thu {selected_date.strftime("%d-%m-%Y")}')
        
        # Định dạng
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 15,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Arial'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F7F7F7',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Arial'
        })
        
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy hh:mm',
            'border': 1,
            'font_name': 'Arial'
        })
        
        money_format = workbook.add_format({
            'num_format': '###,###,### ₫',
            'border': 1,
            'font_name': 'Arial'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'font_name': 'Arial'
        })
        
        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F7F7F7',
            'border': 1,
            'num_format': '###,###,### ₫',
            'font_name': 'Arial'
        })
        
        # Tiêu đề
        worksheet.merge_range('A1:F1', f'BÁO CÁO DOANH THU NGÀY {selected_date.strftime("%d/%m/%Y")}', title_format)
        worksheet.set_row(0, 30)
        
        # Thống kê tổng quan
        total_orders = orders.count()
        completed_orders = orders.filter(status='completed').count()
        pending_orders = orders.filter(status='pending').count()
        
        # Calculate total revenue
        total_revenue = 0
        for order in orders.filter(status='completed'):
            total_revenue += order.get_total() if hasattr(order, 'get_total') and callable(getattr(order, 'get_total')) else 0
        
        row = 3
        worksheet.write(row, 0, 'Tổng số đơn hàng:', cell_format)
        worksheet.write(row, 1, total_orders, cell_format)
        row += 1
        worksheet.write(row, 0, 'Đơn hàng hoàn thành:', cell_format)
        worksheet.write(row, 1, completed_orders, cell_format)
        row += 1
        worksheet.write(row, 0, 'Đơn hàng chờ xử lý:', cell_format)
        worksheet.write(row, 1, pending_orders, cell_format)
        row += 1
        worksheet.write(row, 0, 'Tổng doanh thu:', cell_format)
        worksheet.write(row, 1, total_revenue, money_format)
        
        # Thống kê món ăn bán chạy
        row += 2
        worksheet.merge_range(f'A{row+1}:C{row+1}', 'TOP 5 MÓN BÁN CHẠY NHẤT', header_format)
        row += 1
        worksheet.write(row, 0, 'Món', header_format)
        worksheet.write(row, 1, 'Số lượng', header_format)
        worksheet.write(row, 2, 'Doanh thu', header_format)
        
        # Tính toán số lượng và doanh thu từng món
        menu_items_stats = {}
        for order in orders.filter(status='completed'):
            for item in order.orderitem_set.all():
                if item.menu_item:
                    name = item.menu_item.name
                    price = item.menu_item.price
                elif item.item:
                    name = item.item.name
                    price = item.item.price
                else:
                    continue
                
                if name not in menu_items_stats:
                    menu_items_stats[name] = {'quantity': 0, 'revenue': 0}
                    
                menu_items_stats[name]['quantity'] += item.quantity
                menu_items_stats[name]['revenue'] += price * item.quantity
        
        # Sắp xếp theo số lượng bán giảm dần
        top_items = sorted(
            [{'name': name, **stats} for name, stats in menu_items_stats.items()],
            key=lambda x: x['quantity'],
            reverse=True
        )[:5]  # Lấy 5 món bán chạy nhất
        
        # Thêm thông tin vào worksheet
        for item in top_items:
            row += 1
            worksheet.write(row, 0, item['name'], cell_format)
            worksheet.write(row, 1, item['quantity'], cell_format)
            worksheet.write(row, 2, item['revenue'], money_format)
        
        # Thống kê chi tiết đơn hàng
        row += 3
        worksheet.merge_range(f'A{row+1}:G{row+1}', 'CHI TIẾT ĐƠN HÀNG', header_format)
        row += 1
        worksheet.write(row, 0, 'ID', header_format)
        worksheet.write(row, 1, 'Khách hàng', header_format)
        worksheet.write(row, 2, 'Bàn', header_format)
        worksheet.write(row, 3, 'Thời gian', header_format)
        worksheet.write(row, 4, 'Trạng thái', header_format)
        worksheet.write(row, 5, 'Số món', header_format)
        worksheet.write(row, 6, 'Tổng tiền', header_format)
        
        # Thêm chi tiết từng đơn hàng
        for order in orders.order_by('-created_at'):
            row += 1
            status_map = {
                'pending': 'Chờ xử lý',
                'preparing': 'Đang chuẩn bị',
                'completed': 'Hoàn thành',
                'cancelled': 'Đã hủy'
            }
            
            order_total = order.get_total() if hasattr(order, 'get_total') and callable(getattr(order, 'get_total')) else 0
            
            # Convert to local timezone for display
            local_datetime = timezone.localtime(order.created_at)
            
            worksheet.write(row, 0, order.id, cell_format)
            worksheet.write(row, 1, order.customer_name, cell_format)
            worksheet.write(row, 2, order.table.number if order.table else 'N/A', cell_format)
            worksheet.write_datetime(row, 3, local_datetime.replace(tzinfo=None), date_format)
            worksheet.write(row, 4, status_map.get(order.status, order.status), cell_format)
            worksheet.write(row, 5, order.orderitem_set.count(), cell_format)
            worksheet.write(row, 6, order_total, money_format)
        
        # Điều chỉnh chiều rộng cột
        worksheet.set_column('A:A', 8)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        
        # Đóng workbook
        workbook.close()
        
        # Thiết lập response
        output.seek(0)
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=doanh_thu_ngay_{selected_date.strftime("%d-%m-%Y")}.xlsx'
        return response
    
    def generate_invoices(self, request, queryset):
        """Tạo hóa đơn PDF cho nhiều đơn hàng cùng lúc"""
        if not queryset:
            messages.error(request, "Không có đơn hàng nào được chọn.")
            return
        
        # Lọc ra các đơn hàng hoàn thành
        completed_orders = queryset.filter(status='completed')
        
        if not completed_orders:
            messages.error(request, "Không có đơn hàng hoàn thành nào được chọn. Chỉ đơn hàng hoàn thành mới có thể xuất hóa đơn.")
            return
        
        order_ids = [str(order.id) for order in completed_orders]
        messages.success(request, f"Đã yêu cầu xuất hóa đơn cho {len(completed_orders)} đơn hàng: #{', #'.join(order_ids)}.")
        
        # Redirect đến trang chi tiết đơn hàng đầu tiên
        first_order = completed_orders[0]
        return HttpResponseRedirect(reverse('admin:order_invoice', args=[first_order.id]))
    generate_invoices.short_description = "Xuất hóa đơn PDF cho đơn hàng đã chọn"
    
    def export_monthly_report_excel(self, request):
        """Xuất báo cáo doanh thu theo tháng ra file Excel"""
        # Kiểm tra và cập nhật trạng thái bàn
        # Use the check_table_status method from the admin_site instance (tomcafe_admin_site)
        admin_site = self.admin_site
        if hasattr(admin_site, 'check_table_status'):
            admin_site.check_table_status(request)
        
        # Lấy tháng và năm từ request, nếu không có thì dùng tháng hiện tại
        selected_month = int(request.GET.get('month', timezone.localdate().month))
        selected_year = int(request.GET.get('year', timezone.localdate().year))
        
        # Tạo ngày đầu tháng và cuối tháng
        start_of_month = timezone.make_aware(datetime.datetime(selected_year, selected_month, 1))
        
        # Get the last day of the month
        if selected_month == 12:
            end_of_month = timezone.make_aware(datetime.datetime(selected_year + 1, 1, 1)) - datetime.timedelta(days=1)
        else:
            end_of_month = timezone.make_aware(datetime.datetime(selected_year, selected_month + 1, 1)) - datetime.timedelta(days=1)
        
        end_of_month = timezone.make_aware(datetime.datetime.combine(end_of_month.date(), datetime.time.max))
        
        # Lấy tất cả đơn hàng trong tháng
        orders = Order.objects.filter(created_at__range=(start_of_month, end_of_month))
        completed_orders = orders.filter(status='completed')
        
        # Tạo BytesIO object để lưu file Excel
        output = BytesIO()
        
        # Tạo workbook mới với xlsxwriter
        workbook = xlsxwriter.Workbook(output)
        worksheet_summary = workbook.add_worksheet('Tổng quan')
        worksheet_daily = workbook.add_worksheet('Theo ngày')
        worksheet_items = workbook.add_worksheet('Theo món')
        
        # Định dạng
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 15,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Arial'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F7F7F7',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Arial'
        })
        
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy',
            'border': 1,
            'font_name': 'Arial'
        })
        
        datetime_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy hh:mm',
            'border': 1,
            'font_name': 'Arial'
        })
        
        money_format = workbook.add_format({
            'num_format': '###,###,### ₫',
            'border': 1,
            'font_name': 'Arial'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'font_name': 'Arial'
        })
        
        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F7F7F7',
            'border': 1,
            'num_format': '###,###,### ₫',
            'font_name': 'Arial'
        })
        
        # Tiêu đề cho worksheet tổng quan
        month_names = ['Tháng Một', 'Tháng Hai', 'Tháng Ba', 'Tháng Tư', 'Tháng Năm', 'Tháng Sáu', 
                      'Tháng Bảy', 'Tháng Tám', 'Tháng Chín', 'Tháng Mười', 'Tháng Mười Một', 'Tháng Mười Hai']
        worksheet_summary.merge_range('A1:F1', f'BÁO CÁO DOANH THU {month_names[selected_month-1].upper()} {selected_year}', title_format)
        worksheet_summary.set_row(0, 30)
        
        # Thống kê tổng quan
        total_orders = orders.count()
        total_completed_orders = completed_orders.count()
        
        # Calculate total revenue - safe handling for get_total method
        total_revenue = 0
        for order in completed_orders:
            total_revenue += order.get_total() if hasattr(order, 'get_total') and callable(getattr(order, 'get_total')) else 0
        
        avg_order_value = total_revenue / total_completed_orders if total_completed_orders > 0 else 0
        
        row = 3
        worksheet_summary.write(row, 0, 'Tổng số đơn hàng:', cell_format)
        worksheet_summary.write(row, 1, total_orders, cell_format)
        row += 1
        worksheet_summary.write(row, 0, 'Đơn hàng hoàn thành:', cell_format)
        worksheet_summary.write(row, 1, total_completed_orders, cell_format)
        row += 1
        worksheet_summary.write(row, 0, 'Tổng doanh thu:', cell_format)
        worksheet_summary.write(row, 1, total_revenue, money_format)
        row += 1
        worksheet_summary.write(row, 0, 'Giá trị đơn hàng trung bình:', cell_format)
        worksheet_summary.write(row, 1, avg_order_value, money_format)
        
        # Thống kê doanh thu theo ngày
        row += 3
        worksheet_daily.merge_range('A1:F1', f'DOANH THU THEO NGÀY TRONG {month_names[selected_month-1].upper()} {selected_year}', title_format)
        worksheet_daily.set_row(0, 30)
        
        row = 3
        worksheet_daily.write(row, 0, 'Ngày', header_format)
        worksheet_daily.write(row, 1, 'Số đơn hàng', header_format)
        worksheet_daily.write(row, 2, 'Số đơn hoàn thành', header_format)
        worksheet_daily.write(row, 3, 'Doanh thu', header_format)
        
        # Tạo từ điển để lưu thống kê theo ngày
        daily_stats = {}
        current_date = start_of_month.date()
        while current_date <= end_of_month.date():
            daily_stats[current_date] = {
                'total_orders': 0,
                'completed_orders': 0,
                'revenue': 0
            }
            current_date += datetime.timedelta(days=1)
        
        # Tính toán thống kê theo ngày
        for order in orders:
            order_date = order.created_at.date()
            daily_stats[order_date]['total_orders'] += 1
            if order.status == 'completed':
                daily_stats[order_date]['completed_orders'] += 1
                daily_stats[order_date]['revenue'] += order.get_total() if hasattr(order, 'get_total') and callable(getattr(order, 'get_total')) else 0
        
        # Thêm dữ liệu vào worksheet
        for date, stats in sorted(daily_stats.items()):
            row += 1
            worksheet_daily.write_datetime(row, 0, datetime.datetime.combine(date, datetime.time.min), date_format)
            worksheet_daily.write(row, 1, stats['total_orders'], cell_format)
            worksheet_daily.write(row, 2, stats['completed_orders'], cell_format)
            worksheet_daily.write(row, 3, stats['revenue'], money_format)
        
        # Tổng cộng
        row += 1
        worksheet_daily.write(row, 0, 'Tổng cộng', header_format)
        worksheet_daily.write(row, 1, total_orders, header_format)
        worksheet_daily.write(row, 2, total_completed_orders, header_format)
        worksheet_daily.write(row, 3, total_revenue, total_format)
        
        # Thống kê theo món
        worksheet_items.merge_range('A1:D1', f'DOANH THU THEO MÓN TRONG {month_names[selected_month-1].upper()} {selected_year}', title_format)
        worksheet_items.set_row(0, 30)
        
        row = 3
        worksheet_items.write(row, 0, 'Món', header_format)
        worksheet_items.write(row, 1, 'Số lượng', header_format)
        worksheet_items.write(row, 2, 'Doanh thu', header_format)
        worksheet_items.write(row, 3, 'Tỷ lệ', header_format)
        
        # Tính toán số lượng và doanh thu từng món
        menu_items_stats = {}
        for order in completed_orders:
            for item in order.orderitem_set.all():
                if item.menu_item:
                    name = item.menu_item.name
                    price = item.menu_item.price
                elif item.item:
                    name = item.item.name
                    price = item.item.price
                else:
                    continue
                
                if name not in menu_items_stats:
                    menu_items_stats[name] = {'quantity': 0, 'revenue': 0}
                    
                menu_items_stats[name]['quantity'] += item.quantity
                menu_items_stats[name]['revenue'] += price * item.quantity
        
        # Sắp xếp theo doanh thu giảm dần
        menu_items = sorted(
            [{'name': name, **stats} for name, stats in menu_items_stats.items()],
            key=lambda x: x['revenue'],
            reverse=True
        )
        
        # Thêm thông tin vào worksheet
        for item in menu_items:
            row += 1
            percentage = (item['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            worksheet_items.write(row, 0, item['name'], cell_format)
            worksheet_items.write(row, 1, item['quantity'], cell_format)
            worksheet_items.write(row, 2, item['revenue'], money_format)
            worksheet_items.write(row, 3, f"{percentage:.2f}%", cell_format)
        
        # Điều chỉnh chiều rộng cột
        for sheet in [worksheet_summary, worksheet_daily, worksheet_items]:
            sheet.set_column('A:A', 20)
            sheet.set_column('B:B', 15)
            sheet.set_column('C:C', 15)
            sheet.set_column('D:D', 15)
            sheet.set_column('E:E', 15)
            sheet.set_column('F:F', 15)
        
        # Đóng workbook
        workbook.close()
        
        # Thiết lập response
        output.seek(0)
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=doanh_thu_thang_{selected_month}-{selected_year}.xlsx'
        return response
    
    def get_form(self, request, obj=None, **kwargs):
        # Xử lý các tham số URL để thay đổi trạng thái
        if '_changeto' in request.GET and obj:
            status = request.GET.get('_changeto')
            if status in dict(Order.STATUS_CHOICES).keys():
                obj.status = status
                obj.save()
                if status == 'completed':
                    messages.success(request, f"Đơn hàng #{obj.id} đã được đánh dấu hoàn thành. Bạn có thể xuất hóa đơn ngay bây giờ.")
        return super().get_form(request, obj, **kwargs)
    
    def response_change(self, request, obj):
        # Chuyển hướng đến trang danh sách nếu có tham số _changeto
        if '_changeto' in request.GET:
            return self.response_post_save_change(request, obj)
        return super().response_change(request, obj)

    def num2words_vi(self, num):
        """Chuyển đổi số thành chữ tiếng Việt"""
        if num == 0:
            return "không"
            
        units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
        teens = ["", "mười một", "mười hai", "mười ba", "mười bốn", "mười lăm", "mười sáu", "mười bảy", "mười tám", "mười chín"]
        tens = ["", "mười", "hai mươi", "ba mươi", "bốn mươi", "năm mươi", "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"]
        
        # Xử lý các trường hợp đặc biệt
        if 1 <= num < 10:
            return units[num]
        elif 10 <= num < 20:
            if num == 10:
                return "mười"
            else:
                return teens[num - 10]
        elif 20 <= num < 100:
            unit = num % 10
            ten = num // 10
            if unit == 0:
                return tens[ten]
            elif unit == 1:
                return tens[ten] + " mốt"
            elif unit == 5:
                return tens[ten] + " lăm"
            else:
                return tens[ten] + " " + units[unit]
        elif 100 <= num < 1000:
            hundred = num // 100
            remainder = num % 100
            if remainder == 0:
                return units[hundred] + " trăm"
            else:
                return units[hundred] + " trăm " + self.num2words_vi(remainder)
        elif 1000 <= num < 1000000:
            thousand = num // 1000
            remainder = num % 1000
            if remainder == 0:
                return self.num2words_vi(thousand) + " nghìn"
            else:
                result = self.num2words_vi(thousand) + " nghìn"
                if remainder < 100:
                    result += " không trăm"
                return result + " " + self.num2words_vi(remainder)
        elif 1000000 <= num < 1000000000:
            million = num // 1000000
            remainder = num % 1000000
            if remainder == 0:
                return self.num2words_vi(million) + " triệu"
            else:
                result = self.num2words_vi(million) + " triệu"
                if remainder < 1000:
                    result += " không nghìn"
                return result + " " + self.num2words_vi(remainder)
        else:
            return str(num)  # Fallback cho số quá lớn

    def generate_invoice_pdf(self, request, pk, *args, **kwargs):
        # Biến để lưu log lỗi
        error_logs = []
        
        try:
            error_logs.append("1. Bắt đầu tạo PDF")
            order = get_object_or_404(Order, pk=pk)
            error_logs.append(f"2. Đã tìm đơn hàng #{order.id}")
            
            # Tạo buffer để ghi PDF
            buffer = BytesIO()
            error_logs.append("3. Đã tạo buffer BytesIO")
            
            # Sử dụng phương pháp tìm kiếm font đơn giản và hiệu quả
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            possible_font_locations = [
                os.path.join(base_dir, 'static', 'fonts'),
                os.path.join(base_dir, 'cafe_project', 'static', 'fonts'),
                os.path.join(base_dir, 'staticfiles', 'fonts'),
            ]
            
            # Tìm font trong các thư mục có thể
            font_files = {
                'dejavusans.ttf': None,
                'dejavusans-bold.ttf': None
            }
            
            # Tìm kiếm font
            for font_name in font_files:
                for location in possible_font_locations:
                    font_path = os.path.join(location, font_name)
                    if os.path.exists(font_path) and os.path.getsize(font_path) > 100000:
                        font_files[font_name] = font_path
                        error_logs.append(f"4. Tìm thấy font {font_name} tại {font_path}")
                        break
            
            # Kiểm tra xem có tìm thấy cả hai font không
            if not font_files['dejavusans.ttf'] or not font_files['dejavusans-bold.ttf']:
                error_msg = "Không tìm thấy font DejaVu Sans. Vui lòng chạy script download_vietnamese_fonts.py."
                error_logs.append(f"Lỗi: {error_msg}")
                messages.error(request, error_msg)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        except Exception as e:
            error_msg = f"Lỗi khi tìm font: {str(e)}"
            error_logs.append(error_msg)
            messages.error(request, error_msg)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        # Import các thư viện ReportLab
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.units import cm, mm
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            error_logs.append("5. Đã import thư viện ReportLab")
        except ImportError as e:
            error_msg = f"Lỗi import thư viện ReportLab: {str(e)}"
            error_logs.append(error_msg)
            messages.error(request, error_msg)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        # Đăng ký font DejaVuSans cho tiếng Việt
        try:
            # Kiểm tra xem font đã được đăng ký chưa để tránh đăng ký lại
            if 'DejaVuSans' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('DejaVuSans', font_files['dejavusans.ttf']))
            if 'DejaVuSans-Bold' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_files['dejavusans-bold.ttf']))
            
            # Đăng ký ánh xạ font để đảm bảo tiếng Việt hiển thị đúng
            pdfmetrics.registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans-Bold')
            
            error_logs.append("6. Đã đăng ký font DejaVuSans")
        except Exception as font_error:
            error_msg = f"Lỗi khi đăng ký font: {str(font_error)}"
            error_logs.append(error_msg)
            messages.error(request, error_msg)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        # Tạo document
        try:
            # Sử dụng lề lớn hơn để tạo không gian trắng tốt hơn
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=15*mm,
                leftMargin=15*mm,
                topMargin=15*mm,
                bottomMargin=15*mm
            )
            error_logs.append("7. Đã tạo SimpleDocTemplate")
        except Exception as doc_error:
            error_msg = f"Lỗi khi tạo document: {str(doc_error)}"
            error_logs.append(error_msg)
            messages.error(request, error_msg)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        # Định nghĩa màu sắc
        primary_color = colors.HexColor('#2d2d2d')  # Màu chính - xám đậm
        secondary_color = colors.HexColor('#555555')  # Màu phụ - xám nhạt
        accent_color = colors.HexColor('#8B4513')  # Màu nhấn - nâu cà phê
        light_gray = colors.HexColor('#f5f5f5')  # Màu xám nhạt cho nền
        
        # Tạo styles
        try:
            styles = getSampleStyleSheet()
            
            # Style cho tiêu đề
            styles.add(ParagraphStyle(
                name='TitleStyle', 
                fontName='DejaVuSans-Bold', 
                fontSize=24, 
                alignment=1, 
                spaceAfter=6,
                leading=28,
                textColor=primary_color
            ))
            
            # Style cho tiêu đề phụ
            styles.add(ParagraphStyle(
                name='SubTitleStyle', 
                fontName='DejaVuSans-Bold', 
                fontSize=16, 
                alignment=1, 
                textColor=primary_color,
                spaceBefore=6,
                spaceAfter=6,
                leading=20
            ))
            
            # Style cho địa chỉ
            styles.add(ParagraphStyle(
                name='AddressStyle', 
                fontName='DejaVuSans', 
                fontSize=9, 
                leading=11, 
                alignment=1,
                spaceBefore=2,
                textColor=secondary_color
            ))
            
            # Style cho text thường
            styles.add(ParagraphStyle(
                name='NormalStyle', 
                fontName='DejaVuSans', 
                fontSize=10, 
                leading=12,
                textColor=primary_color
            ))
            
            # Style cho text đậm
            styles.add(ParagraphStyle(
                name='BoldStyle', 
                fontName='DejaVuSans-Bold', 
                fontSize=10, 
                leading=12,
                textColor=primary_color
            ))
            
            # Style cho text thường căn giữa
            styles.add(ParagraphStyle(
                name='NormalCenter', 
                fontName='DejaVuSans', 
                fontSize=10, 
                leading=12,
                alignment=1,
                textColor=primary_color
            ))
            
            # Style cho text thường căn phải
            styles.add(ParagraphStyle(
                name='NormalRight', 
                fontName='DejaVuSans', 
                fontSize=10, 
                leading=12,
                alignment=2,
                textColor=primary_color
            ))
            
            # Style cho text đậm căn phải
            styles.add(ParagraphStyle(
                name='BoldRight', 
                fontName='DejaVuSans-Bold', 
                fontSize=10, 
                leading=12,
                alignment=2,
                textColor=primary_color
            ))
            
            # Style cho header
            styles.add(ParagraphStyle(
                name='HeaderStyle', 
                fontName='DejaVuSans-Bold', 
                fontSize=11, 
                leading=14, 
                alignment=0,
                textColor=primary_color,
                spaceBefore=6,
                spaceAfter=6
            ))
            
            # Style cho header căn giữa
            styles.add(ParagraphStyle(
                name='HeaderCenter', 
                fontName='DejaVuSans-Bold', 
                fontSize=11, 
                leading=14, 
                alignment=1,
                textColor=primary_color
            ))
            
            # Style cho chân trang
            styles.add(ParagraphStyle(
                name='FooterStyle', 
                fontName='DejaVuSans', 
                fontSize=9, 
                leading=11, 
                alignment=1, 
                textColor=secondary_color
            ))
            
            # Style cho số tiền bằng chữ
            styles.add(ParagraphStyle(
                name='AmountWordsStyle', 
                fontName='DejaVuSans-Bold', 
                fontSize=10, 
                leading=12, 
                textColor=primary_color,
                leftIndent=0
            ))
            
            # Style cho lời cảm ơn
            styles.add(ParagraphStyle(
                name='ThankYouStyle', 
                fontName='DejaVuSans-Bold', 
                fontSize=13, 
                leading=16, 
                alignment=1,
                textColor=accent_color,
                spaceBefore=10,
                spaceAfter=10
            ))
            
            error_logs.append("8. Đã tạo styles")
        except Exception as style_error:
            error_msg = f"Lỗi khi tạo styles: {str(style_error)}"
            error_logs.append(error_msg)
            messages.error(request, error_msg)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        # Tạo các phần tử của PDF
        try:
            elements = []
            
            # Thêm khoảng trống ở đầu trang
            elements.append(Spacer(1, 5*mm))
            
            # Tiêu đề TOMCAFE
            elements.append(Paragraph("TOMCAFE", styles['TitleStyle']))
            elements.append(Spacer(1, 3*mm))
            
            # Thông tin địa chỉ
            address_data = [
                [Paragraph("312 Lý Thường Kiệt, TP.Đồng Hới, Quảng Bình", styles['AddressStyle'])],
                [Paragraph("Điện thoại: 0348287671 - Email: tomcafe20@gmail.com", styles['AddressStyle'])],
                [Paragraph("Giờ mở cửa: T2-CN: 08:00 - 22:00", styles['AddressStyle'])]
            ]
            
            address_table = Table(address_data, colWidths=[doc.width])
            address_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (0, 0), 2),
            ]))
            elements.append(address_table)
            
            # Thêm đường kẻ ngang
            elements.append(Spacer(1, 6*mm))
            elements.append(Table([['']], colWidths=[doc.width], rowHeights=[0.5]))
            elements[-1].setStyle(TableStyle([('LINEABOVE', (0, 0), (-1, -1), 1, accent_color)]))
            elements.append(Spacer(1, 6*mm))
            
            # Tiêu đề hóa đơn
            elements.append(Paragraph("HÓA ĐƠN THANH TOÁN", styles['SubTitleStyle']))
            elements.append(Spacer(1, 3*mm))
            
            # Số hóa đơn
            elements.append(Paragraph(f"Số: #{order.id}", styles['BoldStyle']))
            elements.append(Spacer(1, 8*mm))
            
            # Thông tin đơn hàng header
            order_info_header = Table(
                [[Paragraph("Thông tin đơn hàng:", styles['HeaderStyle'])]],
                colWidths=[doc.width]
            )
            order_info_header.setStyle(TableStyle([
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (0, 0), 10),
                ('BOTTOMPADDING', (0, 0), (0, 0), 5),
                ('TOPPADDING', (0, 0), (0, 0), 5),
                ('RIGHTPADDING', (0, 0), (0, 0), 10),
                ('LINEBELOW', (0, 0), (0, 0), 0.5, primary_color),
            ]))
            elements.append(order_info_header)
            elements.append(Spacer(1, 2*mm))
            
            # Thông tin chi tiết đơn hàng
            # Convert order creation date to local timezone
            local_datetime = timezone.localtime(order.created_at)
            formatted_datetime = local_datetime.strftime("%d/%m/%Y %H:%M")
            
            order_details = [
                [Paragraph("Khách hàng:", styles['BoldStyle']), Paragraph(f"{order.customer_name}", styles['NormalStyle'])],
                [Paragraph("Bàn:", styles['BoldStyle']), Paragraph(f"{order.table.number if order.table else 'N/A'}", styles['NormalStyle'])],
                [Paragraph("Ngày:", styles['BoldStyle']), Paragraph(f"{formatted_datetime}", styles['NormalStyle'])],
                [Paragraph("Trạng thái:", styles['BoldStyle']), Paragraph("Hoàn thành", styles['BoldStyle'])]
            ]
            
            order_details_table = Table(order_details, colWidths=[3*cm, 12*cm])
            order_details_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.25, secondary_color),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(order_details_table)
            elements.append(Spacer(1, 8*mm))
            
            # Header cho chi tiết đơn hàng
            order_items_header = Table(
                [[Paragraph("Chi tiết đơn hàng:", styles['HeaderStyle'])]],
                colWidths=[doc.width]
            )
            order_items_header.setStyle(TableStyle([
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (0, 0), 10),
                ('BOTTOMPADDING', (0, 0), (0, 0), 5),
                ('TOPPADDING', (0, 0), (0, 0), 5),
                ('RIGHTPADDING', (0, 0), (0, 0), 10),
                ('LINEBELOW', (0, 0), (0, 0), 0.5, primary_color),
            ]))
            elements.append(order_items_header)
            elements.append(Spacer(1, 2*mm))
            
            # Bảng chi tiết sản phẩm - Sử dụng Paragraph cho tất cả các trường với styles riêng
            items_data = [
                [
                    Paragraph("STT", styles['HeaderCenter']),
                    Paragraph("Sản phẩm", styles['HeaderCenter']),
                    Paragraph("Số lượng", styles['HeaderCenter']),
                    Paragraph("Đơn giá", styles['HeaderCenter']),
                    Paragraph("Thành tiền", styles['HeaderCenter'])
                ]
            ]
            
            total = 0
            item_index = 1
            for item in order.orderitem_set.all():
                if item.menu_item:
                    name = item.menu_item.name
                    price = item.menu_item.price
                elif item.item:
                    name = item.item.name
                    price = item.item.price
                else:
                    continue
                
                subtotal = price * item.quantity
                total += subtotal
                
                # Sử dụng Paragraph với styles riêng cho từng trường
                items_data.append([
                    Paragraph(str(item_index), styles['NormalCenter']),
                    Paragraph(name, styles['NormalStyle']),
                    Paragraph(str(item.quantity), styles['NormalCenter']),
                    Paragraph(f"{price:,.0f}", styles['NormalRight']),
                    Paragraph(f"{subtotal:,.0f}", styles['NormalRight'])
                ])
                
                item_index += 1
            
            # Thêm tổng cộng
            items_data.append([
                Paragraph("", styles['NormalStyle']),
                Paragraph("", styles['NormalStyle']),
                Paragraph("", styles['NormalStyle']),
                Paragraph("Tổng cộng:", styles['BoldRight']),
                Paragraph(f"{total:,.0f}" + "đ", styles['BoldRight'])
            ])
            
            # Định dạng cột cho bảng items
            col_widths = [1.2*cm, 9*cm, 2*cm, 3*cm, 3*cm]
            
            # Tạo bảng sản phẩm
            items_table = Table(items_data, colWidths=col_widths)
            
            # Định dạng bảng
            table_style = [
                # Viền ngoài và lưới bên trong
                ('GRID', (0, 0), (-1, -2), 0.25, secondary_color),
                
                # Căn giữa theo chiều dọc cho tất cả các ô
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                
                # Dòng tổng cộng
                ('LINEABOVE', (3, -1), (4, -1), 1, primary_color),
                ('TOPPADDING', (3, -1), (4, -1), 7),
            ]
            
            items_table.setStyle(TableStyle(table_style))
            elements.append(items_table)
            elements.append(Spacer(1, 8*mm))
            
            # Số tiền bằng chữ
            amount_in_words = "Bằng chữ: " + self.num2words_vi(int(total)).capitalize() + " đồng"
            elements.append(Paragraph(amount_in_words, styles['AmountWordsStyle']))
            elements.append(Spacer(1, 15*mm))
            
            # Thêm dòng cảm ơn
            elements.append(Paragraph("Cảm ơn quý khách đã sử dụng dịch vụ của TomCafe!", styles['ThankYouStyle']))
            
            # Thêm thông tin hóa đơn ở cuối
            elements.append(Spacer(1, 8*mm))
            elements.append(Paragraph(f"Hóa đơn số: #{order.id} - Ngày: {formatted_datetime}", styles['FooterStyle']))
            
            error_logs.append("9. Đã tạo các phần tử PDF")
        except Exception as elements_error:
            error_msg = f"Lỗi khi tạo các phần tử PDF: {str(elements_error)}"
            error_logs.append(error_msg)
            messages.error(request, error_msg)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        # Tạo PDF
        try:
            doc.build(elements)
            error_logs.append("10. Đã tạo PDF thành công")
        except Exception as build_error:
            error_msg = f"Lỗi khi tạo PDF: {str(build_error)}"
            error_logs.append(error_msg)
            messages.error(request, error_msg)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        # Đặt con trỏ về đầu buffer
        buffer.seek(0)
        
        # Tạo phản hồi HTTP với nội dung PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="hoa_don_{order.id}.pdf"'
        response.write(buffer.getvalue())
        
        return response

    def formatted_created_at(self, obj):
        """Display the creation date in the local timezone with proper formatting"""
        local_datetime = timezone.localtime(obj.created_at)
        return local_datetime.strftime("%d/%m/%Y %H:%M")
    formatted_created_at.short_description = 'Ngày tạo'
    formatted_created_at.admin_order_field = 'created_at'
