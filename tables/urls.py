from django.urls import path
from . import views

urlpatterns = [
    path('<int:table_id>/', views.enter_name, name='enter_name'),
    path('', views.table_list, name='table_list'),
]