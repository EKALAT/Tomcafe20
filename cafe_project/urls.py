from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from cafe_project.admin import tomcafe_admin_site

urlpatterns = [
    path('', RedirectView.as_view(url='menu/', permanent=False)),  # สร้าง redirect สำหรับหน้าแรก
    path('grappelli/', include('grappelli.urls')),  # URL สำหรับ Grappelli
    path('admin/', tomcafe_admin_site.urls),  # ใช้ CustomAdmin แทน admin.site เดิม
    path('tables/', include('tables.urls')),
    path('menu/', include('menu.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('customers/', include('customers.urls')),
]

# เพิ่ม URL pattern สำหรับไฟล์ media เมื่ออยู่ใน debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)