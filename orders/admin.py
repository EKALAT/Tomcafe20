from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'table', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name',)
    inlines = [OrderItemInline]
