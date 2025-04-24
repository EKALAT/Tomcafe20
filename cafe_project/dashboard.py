"""
This file was generated with the customdashboard management command, it
contains the two classes for the main dashboard and app index dashboard.
You can customize these classes as you want.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'tomcafe_20.cafe_project.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
import calendar

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name
from orders.views import get_current_month_revenue

class RevenueWidget(modules.DashboardModule):
    """
    Widget hiển thị doanh thu tháng hiện tại
    """
    template = 'admin/widgets/revenue_widget.html'
    
    def __init__(self, title=None, **kwargs):
        super(RevenueWidget, self).__init__(title, **kwargs)
        self.revenue_data = get_current_month_revenue()

class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """
    
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        
        # append revenue widget
        self.children.append(RevenueWidget(
            _("Doanh thu tháng hiện tại"),
            column=1,
            collapsible=False,
        ))
        
        # append a group for "ระบบร้านกาแฟ"
        self.children.append(modules.Group(
            _("ระบบร้านกาแฟ"),
            column=1,
            collapsible=True,
            children=[
                modules.ModelList(
                    _("จัดการโต๊ะ"),
                    column=1,
                    models=('tables.models.Table',),
                ),
                modules.ModelList(
                    _("จัดการเมนู"),
                    column=1,
                    models=('menu.models.MenuItem',),
                ),
                modules.ModelList(
                    _("จัดการออร์เดอร์"),
                    column=1,
                    models=('orders.models.*',),
                ),
                modules.ModelList(
                    _("จัดการลูกค้า"),
                    column=1,
                    models=('customers.models.*',),
                ),
            ]
        ))
        
        # append a group for "จัดการผู้ใช้"
        self.children.append(modules.Group(
            _("จัดการผู้ใช้"),
            column=1,
            collapsible=True,
            children=[
                modules.ModelList(
                    _("Users"),
                    column=1,
                    models=('django.contrib.auth.models.User',
                           'django.contrib.auth.models.Group'),
                ),
            ]
        ))
        
        # append a recent actions module
        self.children.append(modules.RecentActions(
            _("คำสั่งที่ทำล่าสุด"),
            limit=10,
            collapsible=False,
            column=2,
        )) 