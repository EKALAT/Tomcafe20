from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from cafe_project.admin import tomcafe_admin_site

urlpatterns = [
    path('', RedirectView.as_view(url='tables/', permanent=False)),  # Redirect cho trang chủ
    path('grappelli/', include('grappelli.urls')),  # URL cho Grappelli
    path('admin/', tomcafe_admin_site.urls),  # Sử dụng CustomAdmin thay cho admin.site
    path('tables/', include('tables.urls')),
    path('menu/', include('menu.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('customers/', include('customers.urls')),
]

# Phục vụ file media trong mọi trường hợp (cả debug và production)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Phục vụ file static chỉ trong môi trường debug
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)