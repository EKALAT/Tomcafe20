# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Customer

def enter_name(request, table_id):
    if request.method == "POST":
        name = request.POST.get('name')
        request.session['customer_name'] = name
        request.session['table_id'] = table_id
        return redirect('menu')  # ไปหน้าเมนู
    return render(request, 'enter_name.html', {'table_id': table_id})

def register_customer(request):
    if request.method == "POST":
        name = request.POST.get('name')
        request.session['customer_name'] = name
        return redirect('menu_list')  # ไปหน้าเมนู
    return render(request, 'register_customer.html')

def customer_home(request):
    return render(request, 'customers/customer_home.html', {})

# Add other views as needed
