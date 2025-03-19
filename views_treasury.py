from django.views.generic import CreateView, ListView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.contrib import messages
from .models import Treasury, Sale, Purchase, Driver, OilType, Client, CompanyAccount
from .mixins import TransactionManagerRequiredMixin
from django import forms
import datetime
from .models import BalanceChangeLog  # Add import for logging

class TreasuryMovementForm(forms.ModelForm):
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'وارد'),
        ('expense', 'منصرف')
    ]
    
    SOURCE_CHOICES = [
        ('client', 'العميل'),
        ('company', 'الشركة'),
        ('driver', 'السائق')
    ]
    
    transaction_type = forms.ChoiceField(choices=TRANSACTION_TYPE_CHOICES)
    source = forms.ChoiceField(choices=SOURCE_CHOICES, label='نوع الحساب')
    description = forms.CharField(widget=forms.Textarea)
    other_payment_method = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        other_payment = cleaned_data.get('other_payment_method')
        source = cleaned_data.get('source')
        record_id = self.data.get('record_id')

        # Validate payment method
        if payment_method == 'other' and not other_payment:
            self.add_error('other_payment_method', 'يجب إدخال طريقة الدفع عند اختيار "أخرى"')

        # Validate amount
        paid_amount = cleaned_data.get('paid_amount')
        if paid_amount and paid_amount <= 0:
            self.add_error('paid_amount', 'يجب أن يكون المبلغ المدفوع أكبر من الصفر')

        # Validate record selection
        if not record_id:
            self.add_error(None, 'يجب اختيار حساب مرتبط')

        return cleaned_data
    
    class Meta:
        model = Treasury
        fields = ['movement_id', 'date', 'description', 'transaction_type', 'paid_amount', 'payment_method']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'datepicker'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paid_amount'].label = 'المبلغ المدفوع'
        self.fields['payment_method'].label = 'طريقة الدفع'
        self.fields['description'].label = 'ملاحظات'
        self.fields['date'].label = 'التاريخ'
    


class TreasuryListView(LoginRequiredMixin, TransactionManagerRequiredMixin, ListView):
    model = Treasury
    template_name = 'accounts/treasury_list.html'
    context_object_name = 'movements'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(movement_id__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(related_sale__sale_id__icontains=search_query) |
                Q(related_purchase__BU_ID__icontains=search_query) |
                Q(related_driver__name__icontains=search_query)
            )
        
        # Calculate totals for context
        self.income_total = queryset.filter(transaction_type='income').aggregate(total=Sum('paid_amount'))['total'] or 0
        self.expense_total = queryset.filter(transaction_type='expense').aggregate(total=Sum('paid_amount'))['total'] or 0
        
        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['income_total'] = self.income_total
        context['expense_total'] = self.expense_total
        return context

def get_clients(request):
    clients = Client.objects.values('id', 'name', 'balance').order_by('name')
    return JsonResponse({'clients': list(clients)})

def get_drivers(request):
    drivers = Driver.objects.values('id', 'name', 'vehicle_number', 'driver_id').order_by('name')
    return JsonResponse({'drivers': list(drivers)})

class TreasuryCreateView(LoginRequiredMixin, TransactionManagerRequiredMixin, CreateView):
    model = Treasury
    form_class = TreasuryMovementForm
    template_name = 'accounts/treasury_form.html'
    success_url = reverse_lazy('treasury_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sales'] = Sale.objects.all().order_by('-date')
        context['purchases'] = Purchase.objects.all().order_by('-date')
        context['drivers'] = Driver.objects.all().order_by('name')
        return context
    
    def form_valid(self, form):
        try:
            if not form.is_valid():
                if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors.get_json_data(),
                        'non_field_errors': [str(e) for e in form.non_field_errors()]
                    }, status=400)
                return self.form_invalid(form)

            # Get form data
            source = form.cleaned_data['source']
            record_id = self.request.POST.get('record_id')
            paid_amount = form.cleaned_data['paid_amount']
            transaction_type = form.cleaned_data['transaction_type']

            # Handle balance updates based on account type and transaction type
            if record_id:
                try:
                    if source == 'client':
                        client = Client.objects.get(id=record_id)
                        previous_balance = client.balance
                        
                        # Update balance based on transaction type
                        if transaction_type == 'income':
                            client.balance += paid_amount
                        else:  # expense
                            if paid_amount > client.balance:
                                form.add_error('paid_amount', 'المبلغ يتجاوز الرصيد المتاح')
                                return self.form_invalid(form)
                            client.balance -= paid_amount
                            
                        client.save()
                        BalanceChangeLog.objects.create(
                            client=client,
                            user=self.request.user,
                            previous_balance=previous_balance,
                            new_balance=client.balance,
                            change_amount=paid_amount if transaction_type == 'income' else -paid_amount,
                            notes=f"{'إيداع' if transaction_type == 'income' else 'سحب'} خزينة بواسطة {self.request.user.username}"
                        )
                    elif source == 'company':
                        client = Client.objects.get(id=record_id)
                        previous_balance = client.balance
                        
                        # Update balance based on transaction type
                        if transaction_type == 'income':
                            client.balance -= paid_amount  # Deduct from client's balance (company's debt)
                        else:  # expense
                            client.balance += paid_amount  # Add to client's balance
                            
                        client.save()
                        BalanceChangeLog.objects.create(
                            client=client,
                            user=self.request.user,
                            previous_balance=previous_balance,
                            new_balance=client.balance,
                            change_amount=-paid_amount if transaction_type == 'income' else paid_amount,
                            notes=f"{'سحب' if transaction_type == 'income' else 'إيداع'} خزينة بواسطة {self.request.user.username}"
                        )
                    elif source == 'driver':
                        driver = Driver.objects.get(id=record_id)
                        # No balance operations for driver
                        pass
                except Exception as e:
                    form.add_error(None, f'حدث خطأ أثناء الحفظ: {str(e)}')
                    return self.form_invalid(form)

            # Create and save movement
            movement = form.save(commit=False)
            movement.user = self.request.user
            movement.movement_source = source  # Set the movement source based on the selected option
            
            if form.cleaned_data['payment_method'] == 'other':
                movement.payment_details = form.cleaned_data['other_payment_method']
            elif source == 'driver' and record_id:
                driver = get_object_or_404(Driver, id=record_id)
                movement.related_driver = driver
                movement.description = f"دفعة {'إلى' if transaction_type == 'income' else 'من'} حساب السائق {driver.name}"
            elif source == 'client' and record_id:
                client = get_object_or_404(Client, id=record_id)
                movement.related_client = client
                movement.description = f"دفعة {'إلى' if transaction_type == 'income' else 'من'} حساب العميل {client.name}"
            elif source == 'company' and record_id:
                client = get_object_or_404(Client, id=record_id)
                movement.related_client = client
                movement.description = f"دفعة {'إلى' if transaction_type == 'income' else 'من'} حساب الشركة للعميل {client.name}"
            
            # Save the movement record
            movement.save()
            messages.success(self.request, 'تم حفظ حركة الخزينة بنجاح')
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(self.request, f'Error processing transaction: {str(e)}')
            return self.form_invalid(form)

class TreasuryUpdateView(LoginRequiredMixin, TransactionManagerRequiredMixin, UpdateView):
    model = Treasury
    form_class = TreasuryMovementForm
    template_name = 'accounts/treasury_form.html'
    success_url = reverse_lazy('treasury_list')
    
    def get_initial(self):
        initial = super().get_initial()
        if self.object.payment_method == 'other':
            initial['other_payment_method'] = self.object.payment_details
        return initial

    def form_valid(self, form):
        try:
            instance = form.save(commit=False)
            source = form.cleaned_data.get('source')
            paid_amount = form.cleaned_data.get('paid_amount')
            record_id = self.request.POST.get('record_id')
            transaction_type = form.cleaned_data.get('transaction_type')
            
            if not record_id:
                form.add_error(None, 'يجب اختيار حساب مرتبط')
                return self.form_invalid(form)

            # Handle balance updates based on account type and transaction type
            try:
                if source == 'client':
                    client = Client.objects.get(id=record_id)
                    previous_balance = client.balance
                    
                    # Update balance based on transaction type
                    if transaction_type == 'income':
                        client.balance += paid_amount
                    else:  # expense
                        if paid_amount > client.balance:
                            form.add_error('paid_amount', 'المبلغ يتجاوز الرصيد المتاح')
                            return self.form_invalid(form)
                        client.balance -= paid_amount
                        
                    client.save()
                    BalanceChangeLog.objects.create(
                        client=client,
                        user=self.request.user,
                        previous_balance=previous_balance,
                        new_balance=client.balance,
                        change_amount=paid_amount if transaction_type == 'income' else -paid_amount,
                        notes=f"{'إيداع' if transaction_type == 'income' else 'سحب'} خزينة بواسطة {self.request.user.username}"
                    )
                elif source == 'company':
                    client = Client.objects.get(id=record_id)
                    previous_balance = client.balance
                    
                    # Update balance based on transaction type
                    if transaction_type == 'income':
                        client.balance -= paid_amount  # Deduct from client's balance (company's debt)
                    else:  # expense
                        client.balance += paid_amount  # Add to client's balance
                        
                    client.save()
                    BalanceChangeLog.objects.create(
                        client=client,
                        user=self.request.user,
                        previous_balance=previous_balance,
                        new_balance=client.balance,
                        change_amount=-paid_amount if transaction_type == 'income' else paid_amount,
                        notes=f"{'سحب' if transaction_type == 'income' else 'إيداع'} خزينة بواسطة {self.request.user.username}"
                    )
                elif source == 'driver':
                    driver = Driver.objects.get(id=record_id)
                    # No balance operations for driver
                    pass

                # Update movement details
                instance.user = self.request.user
                instance.movement_source = source
                
                if form.cleaned_data['payment_method'] == 'other':
                    instance.payment_details = form.cleaned_data['other_payment_method']
                elif source == 'driver' and record_id:
                    driver = get_object_or_404(Driver, id=record_id)
                    instance.related_driver = driver
                    instance.description = f"دفعة {'إلى' if transaction_type == 'income' else 'من'} حساب السائق {driver.name}"
                elif source == 'client' and record_id:
                    client = get_object_or_404(Client, id=record_id)
                    instance.related_client = client
                    instance.description = f"دفعة {'إلى' if transaction_type == 'income' else 'من'} حساب العميل {client.name}"
                elif source == 'company' and record_id:
                    client = get_object_or_404(Client, id=record_id)
                    instance.related_client = client
                    instance.description = f"دفعة {'إلى' if transaction_type == 'income' else 'من'} حساب الشركة للعميل {client.name}"
                
                instance.save()
                messages.success(self.request, 'تم تحديث حركة الخزينة بنجاح')
                return redirect(self.success_url)

            except Exception as e:
                if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors.get_json_data(),
                        'non_field_errors': [str(e) for e in form.non_field_errors()]
                    }, status=400)
                form.add_error(None, f'حدث خطأ أثناء الحفظ: {str(e)}')
                return self.form_invalid(form)

        except Exception as e:
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error processing transaction: {str(e)}'
                }, status=500)
            messages.error(self.request, f'Error processing transaction: {str(e)}')
            return self.form_invalid(form)

class TreasuryDeleteView(LoginRequiredMixin, TransactionManagerRequiredMixin, DeleteView):
    model = Treasury
    template_name = 'accounts/treasury_confirm_delete.html'
    success_url = reverse_lazy('treasury_list')

# AJAX views for fetching records
def get_sales_json(request):
    sales = Sale.objects.all().order_by('-date')
    data = [{
        'id': sale.id,
        'sale_id': sale.sale_id,
        'client': sale.client.name,
        'date': sale.date.strftime('%Y-%m-%d'),
        'amount': float(sale.total_amount),
        'status': sale.status
    } for sale in sales]
    return JsonResponse({'sales': data})

def get_purchases_json(request):
    purchases = Purchase.objects.all().order_by('-date')
    data = [{
        'id': purchase.id,
        'purchase_id': purchase.BU_ID,
        'supplier': purchase.supplier_name,
        'date': purchase.date.strftime('%Y-%m-%d'),
        'amount': float(purchase.total_amount),
        'status': purchase.status
    } for purchase in purchases]
    return JsonResponse({'purchases': data})

def get_drivers_json(request):
    drivers = Driver.objects.all().order_by('name')
    data = [{
        'id': driver.id,
        'driver_id': driver.driver_id,
        'name': driver.name,
        'vehicle_number': driver.vehicle_number
    } for driver in drivers]
    return JsonResponse({'drivers': data})

def get_clients_json(request):
    clients = Client.objects.all().order_by('name')
    data = [{
        'id': client.id,
        'name': client.name,
        'balance': float(client.balance)
    } for client in clients]
    return JsonResponse({'clients': data})

def get_sale_by_id(request, sale_id):
    try:
        sale = Sale.objects.get(id=sale_id)
        data = {
            'record': {
                'id': sale.id,
                'sale_id': sale.sale_id,
                'client_id': sale.client.id,
                'client_name': sale.client.name,
                'oil_type_id': sale.oil_type.id if sale.oil_type else None,
                'quantity': float(sale.quantity),
                'price': float(sale.price),
                'loading_location': sale.loading_location,
                'unloading_location': sale.unloading_location,
                'driver_id': sale.driver.id if sale.driver else None,
                'driver_name': sale.driver.name if sale.driver else None,
                'driver_freight': 0,  # Default value as it's not in the Sale model
                'client_freight': 0,   # Default value as it's not in the Sale model
            }
        }
        return JsonResponse(data)
    except Sale.DoesNotExist:
        return JsonResponse({'error': 'Sale not found'}, status=404)

def get_purchase_by_id(request, purchase_id):
    try:
        purchase = Purchase.objects.get(id=purchase_id)
        data = {
            'record': {
                'id': purchase.id,
                'purchase_id': purchase.BU_ID,
                'client_id': purchase.client.id,
                'client_name': purchase.client.name,
                'oil_type_id': purchase.oil_type.id if hasattr(purchase, 'oil_type') and purchase.oil_type else None,
                'quantity': float(purchase.quantity),
                'price': float(purchase.price),
                'loading_location': purchase.loading_location,
                'unloading_location': purchase.unloading_location,
                'driver_id': purchase.driver.id if hasattr(purchase, 'driver') and purchase.driver else None,
                'driver_name': purchase.driver.name if hasattr(purchase, 'driver') and purchase.driver else None,
                'driver_freight': 0,  # Default value as it's not in the Purchase model
                'client_freight': 0,   # Default value as it's not in the Purchase model
            }
        }
        return JsonResponse(data)
    except Purchase.DoesNotExist:
        return JsonResponse({'error': 'Purchase not found'}, status=404)