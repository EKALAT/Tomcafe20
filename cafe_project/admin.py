from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
from django.utils import timezone
import datetime
from django.utils.safestring import mark_safe

# ออกแบบ Admin Site ใหม่
class TomCafeAdminSite(AdminSite):
    # เปลี่ยนชื่อหัวเว็บไซต์
    site_title = _("TomCafe Administration")
    site_header = _("TomCafe ระบบจัดการร้านกาแฟ")
    index_title = _("ยินดีต้อนรับสู่ TomCafe Admin")
    
    # เพิ่มข้อมูลสถิติในแดชบอร์ด
    def index(self, request, extra_context=None):
        # นับจำนวนโต๊ะ
        from tables.models import Table
        table_count = Table.objects.count()
        
        # นับจำนวนเมนู
        from menu.models import MenuItem
        menu_count = MenuItem.objects.count()
        
        # นับจำนวนออร์เดอร์วันนี้
        from orders.models import Order
        today = timezone.now().date()
        order_count = Order.objects.filter(
            created_at__date=today
        ).count()
        
        # คำนวณรายได้วันนี้
        today_revenue = 0
        today_orders = Order.objects.filter(created_at__date=today)
        for order in today_orders:
            for item in order.order_items.all():
                today_revenue += item.item.price * item.quantity
        
        # สร้าง context เพิ่มเติม
        my_context = {
            'table_count': table_count,
            'menu_count': menu_count,
            'order_count': order_count,
            'today_revenue': "{:.2f}".format(today_revenue),
        }
        
        # รวม context ที่มีอยู่แล้ว
        if extra_context:
            my_context.update(extra_context)
        
        return super().index(request, my_context)

# สร้าง Instance ของ Admin Site ใหม่
tomcafe_admin_site = TomCafeAdminSite(name='tomcafe_admin')

# ลงทะเบียนโมเดลกับ Admin Site ใหม่
from django.contrib.auth.models import User, Group
from tables.models import Table
from menu.models import MenuItem
from orders.models import Order, OrderItem
from customers.models import Customer

tomcafe_admin_site.register(User)
tomcafe_admin_site.register(Group)

# ลงทะเบียนโมเดล Customer
@admin.register(Customer, site=tomcafe_admin_site)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'visits', 'created_at', 'last_visit')
    list_filter = ('created_at', 'last_visit')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('created_at', 'last_visit')
    fieldsets = (
        ('ข้อมูลลูกค้า', {
            'fields': ('name', 'phone', 'email')
        }),
        ('ข้อมูลการใช้บริการ', {
            'fields': ('visits', 'created_at', 'last_visit')
        }),
    )

# ลงทะเบียนโมเดล Table
@admin.register(Table, site=tomcafe_admin_site)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'status', 'capacity', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('number',)
    list_editable = ('status', 'is_active')
    actions = ['make_available', 'make_unavailable']
    
    def make_available(self, request, queryset):
        queryset.update(status='available')
    make_available.short_description = "ทำให้โต๊ะว่าง"
    
    def make_unavailable(self, request, queryset):
        queryset.update(status='unavailable')
    make_unavailable.short_description = "ทำให้โต๊ะไม่พร้อมใช้งาน"

# ลงทะเบียนโมเดล MenuItem
@admin.register(MenuItem, site=tomcafe_admin_site)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'display_image')
    list_filter = ('category',)
    search_fields = ('name', 'category')
    autocomplete_fields = []
    fieldsets = (
        ('ข้อมูลเมนู', {
            'fields': ('name', 'price', 'category')
        }),
        ('รูปภาพ', {
            'fields': ('image',),
            'description': 'เลือกรูปภาพเมนูที่มีความละเอียดดี (แนะนำขนาด 500x500 px)'
        }),
    )
    
    def display_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="80" height="80" style="object-fit: cover; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" />')
        return "ไม่มีรูปภาพ"
    display_image.short_description = 'รูปภาพ'
    display_image.allow_tags = True

# ลงทะเบียนโมเดล Order และ OrderItem
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ['item']

@admin.register(Order, site=tomcafe_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'table', 'created_at', 'status', 'order_total')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'table__number')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    actions = ['mark_as_done', 'mark_as_waiting']
    
    def order_total(self, obj):
        total = sum(item.item.price * item.quantity for item in obj.order_items.all())
        return f"{total:.2f} บาท"
    order_total.short_description = 'ยอดรวม'
    
    def mark_as_done(self, request, queryset):
        queryset.update(status='done')
    mark_as_done.short_description = "ทำเครื่องหมายว่าเสร็จสิ้น"
    
    def mark_as_waiting(self, request, queryset):
        queryset.update(status='waiting')
    mark_as_waiting.short_description = "ทำเครื่องหมายว่ารอดำเนินการ" 