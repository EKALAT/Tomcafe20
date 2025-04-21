"""
This file was generated with the customdashboard management command, it
contains the two classes for the main dashboard and app index dashboard.
You can customize these classes as you want.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'tomcafe_20.cafe_project.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """
    
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        
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