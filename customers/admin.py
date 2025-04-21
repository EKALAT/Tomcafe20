from django.contrib import admin
from .models import Customer

@admin.register(Customer)
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
