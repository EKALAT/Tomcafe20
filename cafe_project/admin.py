from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
from django.utils import timezone
import datetime
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import AdminFileWidget
from django.db.models import Sum, F, DecimalField

# Thiết kế Admin Site mới
class TomCafeAdminSite(AdminSite):
    # Thiết lập tên tiêu đề trang
    site_title = _("TomCafe - Quản lý")
    site_header = _("TomCafe - Hệ thống quản lý quán cà phê")
    index_title = _("Chào mừng đến với TomCafe Admin")
    
    # Thêm thông tin thống kê vào dashboard
    def index(self, request, extra_context=None):
        # Đếm số bàn
        from tables.models import Table
        table_count = Table.objects.count()
        available_tables = Table.objects.filter(status='available', is_active=True).count()
        
        # Đếm số món trong menu
        from menu.models import MenuItem
        menu_count = MenuItem.objects.count()
        
        # Đếm số đơn hàng hôm nay
        from orders.models import Order
        today = timezone.now().date()
        order_count = Order.objects.filter(
            created_at__date=today
        ).count()
        
        # Tính doanh thu hôm nay
        today_revenue = 0
        today_orders = Order.objects.filter(created_at__date=today)
        for order in today_orders:
            for item in order.order_items.all():
                today_revenue += item.item.price * item.quantity
        
        # Tình trạng đơn hàng
        pending_orders = Order.objects.filter(status='waiting').count()
        done_orders = Order.objects.filter(status='done').count()
        
        # Đếm số khách hàng và người dùng
        from customers.models import Customer
        from django.contrib.auth.models import User
        customer_count = Customer.objects.count()
        user_count = User.objects.count()
        
        # Tạo context bổ sung
        my_context = {
            'table_count': table_count,
            'available_tables': available_tables,
            'menu_count': menu_count,
            'order_count': order_count,
            'today_revenue': "{:,.2f}".format(today_revenue).replace(',', '.'),
            'pending_orders': pending_orders,
            'done_orders': done_orders,
            'customer_count': customer_count,
            'user_count': user_count,
        }
        
        # Kết hợp với context hiện có
        if extra_context:
            my_context.update(extra_context)
        
        return super().index(request, my_context)

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
    list_display = ('name', 'phone', 'email', 'visits', 'created_at', 'last_visit')
    list_filter = ('created_at', 'last_visit')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('created_at', 'last_visit')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Thông tin khách hàng', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Thông tin sử dụng dịch vụ', {
            'fields': ('visits', 'created_at', 'last_visit')
        }),
    )

# Đăng ký model Table
@admin.register(Table, site=tomcafe_admin_site)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'get_status_display', 'capacity', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('number',)
    list_editable = ('is_active',)
    actions = ['make_available', 'make_unavailable']
    
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
    list_display = ('name', 'format_price', 'category', 'display_image')
    list_filter = ('category',)
    search_fields = ('name', 'category')
    autocomplete_fields = []
    
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
            'fields': ('name', 'price', 'category')
        }),
        ('Hình ảnh', {
            'fields': ('image',),
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
    extra = 1
    autocomplete_fields = ['item']
    readonly_fields = ['item_price', 'item_total']
    
    def item_price(self, obj):
        if obj.item:
            return f"{obj.item.price:,.0f} đ"
        return "-"
    item_price.short_description = "Giá đơn vị"
    
    def item_total(self, obj):
        if obj.item:
            return f"{obj.item.price * obj.quantity:,.0f} đ"
        return "-"
    item_total.short_description = "Thành tiền"

@admin.register(Order, site=tomcafe_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'table', 'created_at', 'get_status_display', 'order_total')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'table__number')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    actions = ['mark_as_done', 'mark_as_waiting']
    
    def get_status_display(self, obj):
        status_map = {
            'waiting': '<span style="color:orange; font-weight:bold;">Đang chờ</span>',
            'processing': '<span style="color:blue; font-weight:bold;">Đang xử lý</span>',
            'done': '<span style="color:green; font-weight:bold;">Hoàn thành</span>',
            'cancelled': '<span style="color:red; font-weight:bold;">Đã hủy</span>',
        }
        return mark_safe(status_map.get(obj.status, obj.status))
    get_status_display.short_description = 'Trạng thái'
    
    def order_total(self, obj):
        total = sum(item.item.price * item.quantity for item in obj.order_items.all())
        return f"{total:,.0f} đ"
    order_total.short_description = 'Tổng tiền'
    
    def mark_as_done(self, request, queryset):
        queryset.update(status='done')
    mark_as_done.short_description = "Đánh dấu hoàn thành"
    
    def mark_as_waiting(self, request, queryset):
        queryset.update(status='waiting')
    mark_as_waiting.short_description = "Đánh dấu đang chờ xử lý" 