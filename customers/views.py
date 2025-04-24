# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Customer
from tables.models import Table

def enter_name(request, table_id):
    if request.method == "POST":
        name = request.POST.get('name')
        # Lưu thông tin vào session
        request.session['customer_name'] = name
        request.session['table_id'] = table_id
        
        # In thông tin để debug
        print(f"ENTER_NAME Session data: customer_name={name}, table_id={table_id}")
        
        return redirect('menu_list')  # Đến trang thực đơn
        
    # Lấy thông tin bàn để hiển thị
    try:
        table = Table.objects.get(id=table_id)
        table_number = table.number
    except Table.DoesNotExist:
        table_number = "Không xác định"
        
    return render(request, 'customers/enter_name.html', {'table_id': table_id, 'table_number': table_number})

def register_customer(request):
    if request.method == "POST":
        name = request.POST.get('name')
        # Lưu tên khách hàng
        request.session['customer_name'] = name
        # Nếu không có table_id, sử dụng giá trị mặc định
        if 'table_id' not in request.session:
            request.session['table_id'] = 1
            
        # In thông tin để debug
        print(f"REGISTER_CUSTOMER Session data: customer_name={name}, table_id={request.session.get('table_id')}")
        
        return redirect('menu_list')  # Đến trang thực đơn
    return render(request, 'customers/register_customer.html')

def customer_home(request):
    return render(request, 'customers/customer_home.html', {})

# Add other views as needed
