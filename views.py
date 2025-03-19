from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, RedirectView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect, render
from .mixins import AdminRequiredMixin, ClientManagerRequiredMixin, VehicleManagerRequiredMixin
from .models import Client, Driver, CustomUser, BalanceChangeLog, OilType, Sale, Purchase, Treasury
from django.shortcuts import redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.contrib import messages
from .forms import LoginForm, PurchaseForm

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "تم تسجيل الدخول بنجاح")
                return redirect('home')
            else:
                messages.error(request, "خطأ في اسم المستخدم أو كلمة المرور")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, "تم تسجيل الخروج بنجاح")
        return redirect('login')
    return redirect('home')

class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

class RoleRequiredMixin:
    """A mixin that allows specific roles to access a view"""
    required_roles = ['admin']
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in self.required_roles:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

class ClientManagerRequiredMixin(RoleRequiredMixin):
    required_roles = ['admin', 'client_manager']



class HomeView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.role == 'admin':
                return reverse_lazy('user_list')
            return reverse_lazy('client_list')
        return reverse_lazy('login')

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = CustomUser
    fields = ['username', 'password', 'role']
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.role = form.cleaned_data['role']
        user.save()
        
        # Automatically log the user in after registration
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super().form_valid(form)


# Client Views
class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'accounts/client_list.html'
    context_object_name = 'clients'

class ClientCreateView(LoginRequiredMixin, ClientManagerRequiredMixin, CreateView):
    model = Client
    fields = ['name', 'company_name', 'address', 'phone_number', 'commercial_reg_number', 'bank_account_number', 'balance']
    template_name = 'accounts/client_form.html'
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        # Remove the created_by assignment as it doesn't exist in the Client model
        return super().form_valid(form)

class ClientUpdateView(LoginRequiredMixin, ClientManagerRequiredMixin, UpdateView):
    model = Client
    fields = ['name', 'company_name', 'address', 'phone_number', 'commercial_reg_number', 'bank_account_number', 'balance']
    template_name = 'accounts/client_form.html'
    success_url = reverse_lazy('client_list')
    
    def form_valid(self, form):
        # Get the original client instance from the database
        original_client = Client.objects.get(pk=self.object.pk)
        original_balance = original_client.balance
        
        # Call the parent's form_valid method to save the form
        response = super().form_valid(form)
        
        # Check if balance has changed
        new_balance = form.instance.balance
        if original_balance != new_balance:
            # Create a balance change log entry
            BalanceChangeLog.objects.create(
                client=form.instance,
                user=self.request.user,
                previous_balance=original_balance,
                new_balance=new_balance,
                change_amount=new_balance - original_balance,
                notes=f"Balance updated by {self.request.user.username}"
            )
        
        return response

class ClientDeleteView(LoginRequiredMixin, ClientManagerRequiredMixin, DeleteView):
    model = Client
    template_name = 'accounts/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')

# Driver Views
class DriverListView(LoginRequiredMixin, VehicleManagerRequiredMixin, ListView):
    model = Driver
    template_name = 'accounts/driver_list.html'
    context_object_name = 'drivers'

class DriverCreateView(LoginRequiredMixin, VehicleManagerRequiredMixin, CreateView):
    model = Driver
    fields = ['name', 'id_number', 'address', 'phone_number', 'license_number', 'license_type', 'license_expiry_date', 'vehicle_number', 'vehicle_type']
    template_name = 'accounts/driver_form.html'
    success_url = reverse_lazy('driver_list')

class DriverUpdateView(LoginRequiredMixin, VehicleManagerRequiredMixin, UpdateView):
    model = Driver
    fields = ['name', 'id_number', 'address', 'phone_number', 'license_number', 'license_type', 'license_expiry_date', 'vehicle_number', 'vehicle_type']
    template_name = 'accounts/driver_form.html'
    success_url = reverse_lazy('driver_list')

class DriverDeleteView(LoginRequiredMixin, VehicleManagerRequiredMixin, DeleteView):
    model = Driver
    template_name = 'accounts/driver_confirm_delete.html'
    success_url = reverse_lazy('driver_list')



class OilTypeListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = OilType
    template_name = 'accounts/oiltype_list.html'
    context_object_name = 'oiltypes'

    paginate_by = 10

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        queryset = OilType.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(properties__icontains=search_query)
            )
        return queryset.order_by('id')

class OilTypeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = OilType
    fields = ['name', 'properties', 'notes']
    template_name = 'accounts/oiltype_form.html'
    success_url = reverse_lazy('oiltype_list')

class OilTypeUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = OilType
    fields = ['name', 'properties', 'notes']
    template_name = 'accounts/oiltype_form.html'
    success_url = reverse_lazy('oiltype_list')

class OilTypeDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = OilType
    template_name = 'accounts/oiltype_confirm_delete.html'
    success_url = reverse_lazy('oiltype_list')

class PurchaseCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'accounts/purchase_form.html'
    success_url = reverse_lazy('purchase_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = Client.objects.all().order_by('name')
        return context

    def form_valid(self, form):
        return super().form_valid(form)

class PurchaseUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'accounts/purchase_form.html'
    success_url = reverse_lazy('purchase_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = Client.objects.all().order_by('name')
        return context

class PurchaseDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Purchase
    template_name = 'accounts/purchase_confirm_delete.html'
    success_url = reverse_lazy('purchase_list')

class PurchaseListView(LoginRequiredMixin, ListView):
    model = Purchase
    template_name = 'accounts/purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(client__name__icontains=search_query) |
                Q(oil_type__name__icontains=search_query) |
                Q(driver__name__icontains=search_query)
            )
        return queryset

class SaleCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Sale
    fields = ['date', 'client', 'oil_type', 'quantity', 'price', 'loading_location', 'unloading_location', 'driver', 'description']
    template_name = 'accounts/sale_form.html'
    success_url = reverse_lazy('sale_list')

    def form_valid(self, form):
        if not form.instance.sale_id:
            last_sale = Sale.objects.select_for_update().order_by('-sale_id').first()
            if last_sale and last_sale.sale_id:
                try:
                    last_number = int(last_sale.sale_id.split('-')[1])
                    new_number = last_number + 1
                except (IndexError, ValueError):
                    new_number = 1
            else:
                new_number = 1
            form.instance.sale_id = f'SL-{new_number:03d}'
        return super().form_valid(form)

class SaleUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Sale
    fields = ['date', 'client', 'oil_type', 'quantity', 'price', 'loading_location', 'unloading_location', 'driver', 'description']
    template_name = 'accounts/sale_form.html'
    success_url = reverse_lazy('sale_list')

class SaleDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Sale
    template_name = 'accounts/sale_confirm_delete.html'
    success_url = reverse_lazy('sale_list')

class SaleListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'accounts/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(client__name__icontains=search_query) |
                Q(oil_type__name__icontains=search_query) |
                Q(driver__name__icontains=search_query)
            )
        return queryset

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')

class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = CustomUser
    fields = ['username', 'password', 'role']
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        user = form.save(commit=False)
        if form.cleaned_data['password']:
            user.set_password(form.cleaned_data['password'])
        user.save()
        return super().form_valid(form)

class UserPermissionsGuideView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/user_permissions_guide.html'

class ClientBalanceLogsView(LoginRequiredMixin, ClientManagerRequiredMixin, DetailView):
    model = Client
    template_name = 'accounts/client_balance_logs.html'
    context_object_name = 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        context['balance_logs'] = BalanceChangeLog.objects.filter(client=client).order_by('-timestamp')
        return context

# Client Statement View
class ClientStatementView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/client_statement.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = Client.objects.all().order_by('name')
        
        client_id = self.request.GET.get('client_id')
        if client_id:
            client = get_object_or_404(Client, id=client_id)
            context['client'] = client
            
            # Get all sales for this client
            sales = Sale.objects.filter(client=client).order_by('date')
            
            # Get all purchases for this client (as supplier)
            purchases = Purchase.objects.filter(supplier=client).order_by('date')
            
            # Get all treasury movements for this client
            treasury_movements = Treasury.objects.filter(related_client=client).order_by('date')
            
            # Calculate totals
            total_sales = sales.aggregate(total=Sum('amount'))['total'] or 0
            total_purchases = purchases.aggregate(total=Sum('amount'))['total'] or 0
            total_treasury = treasury_movements.aggregate(total=Sum('paid_amount'))['total'] or 0
            
            context['total_sales'] = total_sales
            context['total_purchases'] = total_purchases
            context['total_treasury'] = total_treasury
            
            # Combine all transactions into a single list
            transactions = []
            
            # Add sales transactions
            for sale in sales:
                transactions.append({
                    'date': sale.date,
                    'transaction_id': sale.sale_id,
                    'type': 'sale',
                    'details': f'بيع {sale.quantity} {sale.oil_type.name if sale.oil_type else ""}',
                    'amount': sale.amount,
                    'balance': 0  # Will calculate running balance later
                })
            
            # Add purchase transactions
            for purchase in purchases:
                transactions.append({
                    'date': purchase.date,
                    'transaction_id': purchase.BU_ID,
                    'type': 'purchase',
                    'details': f'شراء {purchase.quantity} {purchase.oil_type.name if purchase.oil_type else ""}',
                    'amount': -purchase.amount,  # Negative amount for purchases
                    'balance': 0  # Will calculate running balance later
                })
            
            # Add treasury transactions
            for movement in treasury_movements:
                amount = movement.paid_amount
                if movement.transaction_type == 'expense':
                    amount = -amount  # Negative for expenses
                
                transactions.append({
                    'date': movement.date,
                    'transaction_id': f'TR-{movement.movement_id}',
                    'type': 'treasury',
                    'details': movement.description,
                    'amount': amount,
                    'balance': 0  # Will calculate running balance later
                })
            
            # Sort transactions by date
            transactions.sort(key=lambda x: x['date'])
            
            # Calculate running balance
            running_balance = 0
            for transaction in transactions:
                running_balance += transaction['amount']
                transaction['balance'] = running_balance
            
            context['transactions'] = transactions
        
        return context