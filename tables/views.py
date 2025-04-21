from django.shortcuts import render, redirect
from .models import Table

def enter_name(request, table_id):
    if request.method == "POST":
        name = request.POST.get('name')
        request.session['customer_name'] = name
        request.session['table_id'] = table_id
        return redirect('menu_list')
    return render(request, 'customers/enter_name.html', {'table_id': table_id})

def table_list(request):
    tables = Table.objects.all()
    return render(request, 'tables/table_list.html', {'tables': tables})
