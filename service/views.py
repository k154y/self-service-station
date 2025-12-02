from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from .models import *
from django.http import HttpResponseForbidden,JsonResponse
from django.contrib.auth.decorators import user_passes_test

# AUTHENTICATION VIEWS 
def landing_page(request):
    """Landing page - Login screen"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            if user.password == password:
                request.session['user_id'] = user.user_id
                request.session['username'] = user.username
                request.session['role'] = user.role
                request.session['full_name'] = user.full_name
                messages.success(request, f'Welcome back, {user.full_name}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials')
        except User.DoesNotExist:
            messages.error(request, 'User does not exist')
    
    return render(request, 'landing.html')

def signup_page(request):
    """Sign up page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'manager')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        else:
            user = User.objects.create(
                username=username,
                full_name=full_name,
                email=email,
                password=password,
                role=role
            )
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('landing_page')
    
    return render(request, 'signup.html')

def forgot_password(request):
    """Forgot password page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            messages.success(request, 'Please check your email for a confirmation link')
            return redirect('landing_page')
        except User.DoesNotExist:
            messages.error(request, 'Email not found')
    
    return render(request, 'forgot_password.html')

def user_logout(request):
    """Logout user"""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully')
    return redirect('landing_page')

def dashboard(request):
    """Main dashboard after login"""
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    
    if not user_id:
        return redirect('landing_page')
    
    try:
        user = User.objects.get(user_id=user_id)
        stations = get_user_stations(user_id, user_role)
        
        # Get dashboard data
        pumps = Pump.objects.filter(station__in=stations)
        active_pumps = pumps.filter(status='active').count()
        offline_pumps = pumps.filter(status='offline').count()
        
        # Today's revenue and fuel dispensed
        today = timezone.now().date()
        today_data = Transaction.objects.filter(
            station_id__in=stations,
            transaction_time__date=today
        ).aggregate(
            total_revenue=Sum('total_price'),
            petrol_dispensed=Sum('quantity', filter=Q(fuel_type='Petrol')),
            diesel_dispensed=Sum('quantity', filter=Q(fuel_type='Diesel'))
        )
        
        today_revenue = today_data['total_revenue'] or 0
        petrol_dispensed = today_data['petrol_dispensed'] or 0
        diesel_dispensed = today_data['diesel_dispensed'] or 0
        
        # Recent transactions
        recent_transactions = Transaction.objects.filter(
            station_id__in=stations
        ).order_by('-transaction_time')[:5]
        
        # Alerts
        alerts = Alert.objects.filter(station__in=stations, status='pending')
        
        context = {
            'user': user,
            'stations': stations,
            'pumps': pumps,
            'active_pumps_count': active_pumps,
            'offline_pumps_count': offline_pumps,
            'today_revenue': today_revenue,
            'petrol_dispensed': petrol_dispensed,
            'diesel_dispensed': diesel_dispensed,
            'recent_transactions': recent_transactions,
            'alerts': alerts,
        }
        
        return render(request, 'dashboard.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('landing_page')

#  HELPER FUNCTIONS 
def get_user_stations(user_id, user_role):
    """
    Returns a QuerySet of Station objects the user has access to.
    """
    if not user_id:
        return Station.objects.none()

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return Station.objects.none()

    if user_role == 'Admin':
        # Admin sees all stations across all companies
        return Station.objects.all()

    elif user_role == 'Owner':
        # Owner sees stations associated with companies they own
        return Station.objects.filter(company_id__owner=user)

    elif user_role == 'Manager':
        # Manager sees stations they are assigned to manage
        return Station.objects.filter(manager_id=user)

    return Station.objects.none()

# USER CRUD (Class-Based Views) 
class UserListView(ListView):
    model = User
    template_name = "users/list.html"
    context_object_name = "users"

class UserCreateView(CreateView):
    model = User
    template_name = "users/form.html"
    fields = ["username", "full_name", "email", "password", "role"]
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'User created successfully!')
        return super().form_valid(form)

class UserUpdateView(UpdateView):
    model = User
    template_name = "users/form.html"
    fields = ["username", "full_name", "email", "password", "role"]
    success_url = reverse_lazy('user_list')
    pk_url_kwarg = 'user_id'
    
    def form_valid(self, form):
        messages.success(self.request, 'User updated successfully!')
        return super().form_valid(form)

class UserDeleteView(DeleteView):
    model = User
    template_name = "users/confirm_delete.html"
    success_url = reverse_lazy('user_list')
    pk_url_kwarg = 'user_id'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'User deleted successfully!')
        return super().delete(request, *args, **kwargs)

# ========== COMPANY CRUD ==========
class CompanyListView(ListView):
    model = Company
    template_name = "companies/list.html"
    context_object_name = "companies"

class CompanyCreateView(CreateView):
    model = Company
    template_name = "companies/form.html"
    fields = ["name", "owner"]
    success_url = reverse_lazy('company_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Company created successfully!')
        return super().form_valid(form)

class CompanyUpdateView(UpdateView):
    model = Company
    template_name = "companies/form.html"
    fields = ["name", "owner"]
    success_url = reverse_lazy('company_list')
    pk_url_kwarg = 'company_id'
    
    def form_valid(self, form):
        messages.success(self.request, 'Company updated successfully!')
        return super().form_valid(form)

class CompanyDeleteView(DeleteView):
    model = Company
    template_name = "companies/confirm_delete.html"
    success_url = reverse_lazy('company_list')
    pk_url_kwarg = 'company_id'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Company deleted successfully!')
        return super().delete(request, *args, **kwargs)

# ========== STATION CRUD ==========
class StationListView(ListView):
    model = Station
    template_name = "stations/list.html"
    context_object_name = "stations"
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        return get_user_stations(user_id, user_role)

class StationCreateView(CreateView):
    model = Station
    template_name = "stations/form.html"
    fields = ["company_id", "manager_id", "name", "location", "status"]
    success_url = reverse_lazy('station_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Station created successfully!')
        return super().form_valid(form)

class StationUpdateView(UpdateView):
    model = Station
    template_name = "stations/form.html"
    fields = ["company_id", "manager_id", "name", "location", "status"]
    success_url = reverse_lazy('station_list')
    pk_url_kwarg = 'station_id'
    
    def form_valid(self, form):
        messages.success(self.request, 'Station updated successfully!')
        return super().form_valid(form)

class StationDeleteView(DeleteView):
    model = Station
    template_name = "stations/confirm_delete.html"
    success_url = reverse_lazy('station_list')
    pk_url_kwarg = 'station_id'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Station deleted successfully!')
        return super().delete(request, *args, **kwargs)

# ========== PUMP CRUD ==========
class PumpListView(ListView):
    model = Pump
    template_name = "pumps/list.html"
    context_object_name = "pumps"
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        return Pump.objects.filter(station__in=stations)

class PumpCreateView(CreateView):
    model = Pump
    template_name = "pumps/form.html"
    fields = ["station", "pump_number", "fuel_type", "status", "flow_rate"]
    success_url = reverse_lazy('pump_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Pump created successfully!')
        return super().form_valid(form)

class PumpUpdateView(UpdateView):
    model = Pump
    template_name = "pumps/form.html"
    fields = ["station", "pump_number", "fuel_type", "status", "flow_rate"]
    success_url = reverse_lazy('pump_list')
    pk_url_kwarg = 'pump_id'
    
    def form_valid(self, form):
        messages.success(self.request, 'Pump updated successfully!')
        return super().form_valid(form)

class PumpDeleteView(DeleteView):
    model = Pump
    template_name = "pumps/confirm_delete.html"
    success_url = reverse_lazy('pump_list')
    pk_url_kwarg = 'pump_id'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Pump deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Special function-based view for quick status update
def pump_status_update(request, pump_id):
    """Quick status update"""
    pump = get_object_or_404(Pump, pump_id=pump_id)
    if request.method == 'POST':
        pump.status = request.POST.get('status')
        pump.save()
        messages.success(request, f'Pump {pump.pump_number} status updated!')
        return redirect('pump_list')
    return render(request, 'pumps/status_update.html', {'pump': pump})

# ========== INVENTORY CRUD ==========
class InventoryListView(ListView):
    model = Inventory
    template_name = "inventory/list.html"
    context_object_name = "inventory"
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        inventory = Inventory.objects.filter(station_id__in=stations)
        
        # Calculate percentages
        for item in inventory:
            item.percentage = (item.quantity / item.capacity) * 100
            if item.percentage >= 75:
                item.status = 'Good'
            elif item.percentage >= 50:
                item.status = 'Medium'
            else:
                item.status = 'Low'
        
        return inventory

class InventoryUpdateView(UpdateView):
    model = Inventory
    template_name = "inventory/form.html"
    fields = ["quantity", "unit_price", "min_threshold"]
    success_url = reverse_lazy('inventory_list')
    pk_url_kwarg = 'inventory_id'
    
    def form_valid(self, form):
        messages.success(self.request, 'Inventory updated successfully!')
        return super().form_valid(form)

class InventoryAccessMixin(UserPassesTestMixin):
    """Ensures the user is logged in before accessing inventory pages."""
    def test_func(self):
        return self.request.session.get('user_id') and self.request.session.get('role')

    def handle_no_permission(self):
        if not self.request.session.get('user_id'):
            return redirect(reverse_lazy('landing_page')) # Redirect to login if not logged in
        return HttpResponseForbidden("You do not have permission to view this page.")

# ========== INVENTORY CRUD ==========

class InventoryListView(InventoryAccessMixin, ListView):
    model = Inventory
    template_name = "inventory/list.html"
    context_object_name = "inventory_list"

    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        inventory = Inventory.objects.filter(station_id__in=stations)
        
        # Calculate percentages and status for display
        for item in inventory:
            if item.capacity and item.capacity > 0:
                # *** THIS IS THE KEY CALCULATION ***
                item.percentage = (item.quantity / item.capacity) * 100 
            else:
                item.percentage = 0
            
            # ... status calculation ...
            
        return inventory
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_role = self.request.session.get('role')
        
        # Pass a flag to control the visibility of the "Edit" button in the template
        # Only Admin and Owner can edit, Managers can only view.
        context['can_edit'] = user_role in ['Admin', 'Owner']
        context['user_role'] = user_role
        return context


class InventoryUpdateView(InventoryAccessMixin, UpdateView):
    model = Inventory
    template_name = "inventory/inventory_update.html" # Renamed to match my previous suggestion
    fields = ["quantity", "unit_price", "min_threshold"]
    success_url = reverse_lazy('inventory_list')
    pk_url_kwarg = 'inventory_id'
    
    # Enforce role-based access for UPDATING
    def test_func(self):
        # 1. Check base access (logged in)
        if not super().test_func():
            return False
        
        user_role = self.request.session.get('role')
        user_id = self.request.session.get('user_id')
        
        # Admin can update everything
        if user_role == 'Admin':
            return True
            
        # Managers are not allowed to update
        if user_role == 'Manager':
            return False 
        
        # Owner check: Must own the company associated with the station
        if user_role == 'Owner':
            inventory = self.get_object() # Fetches the Inventory item being updated
            try:
                current_user = User.objects.get(pk=user_id)
                # Check if the current user is the owner of the company associated with the station
                return inventory.station_id.company_id.owner == current_user
            except User.DoesNotExist:
                return False
        
        return False

    def form_valid(self, form):
        messages.success(self.request, 'Inventory updated successfully!')
        return super().form_valid(form)

# ========== TRANSACTION CRUD ==========
class TransactionListView(ListView):
    model = Transaction
    template_name = "transactions/list.html"
    context_object_name = "transactions"
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        transactions = Transaction.objects.filter(station_id__in=stations)
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            transactions = transactions.filter(
                Q(fuel_type__icontains=search_query) |
                Q(payment_method__icontains=search_query) |
                Q(car_plate__icontains=search_query)
            )
        
        return transactions
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        
        # Today's totals
        today = timezone.now().date()
        today_totals = Transaction.objects.filter(
            station_id__in=stations,
            transaction_time__date=today
        ).aggregate(
            total_revenue=Sum('total_price'),
            total_transactions=Sum('quantity')
        )
        
        context['search_query'] = self.request.GET.get('search', '')
        context['total_transactions'] = context['transactions'].count()
        context['today_revenue'] = today_totals['total_revenue'] or 0
        context['total_petrol'] = context['transactions'].filter(fuel_type='Petrol').aggregate(Sum('quantity'))['quantity__sum'] or 0
        context['total_diesel'] = context['transactions'].filter(fuel_type='Diesel').aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        return context

class TransactionCreateView(CreateView):
    model = Transaction
    template_name = "transactions/form.html"
    fields = ["station_id", "pump_id", "fuel_type", "quantity", "payment_method", "car_plate"]
    success_url = reverse_lazy('transaction_list')
    
    def form_valid(self, form):
        # Set the user_id from session
        form.instance.user_id_id = self.request.session.get('user_id')
        
        # Calculate total price
        fuel_type = form.cleaned_data['fuel_type']
        quantity = form.cleaned_data['quantity']
        
        try:
            price_setting = SystemSetting.objects.get(fuel_type=fuel_type)
            form.instance.total_price = quantity * price_setting.price_per_liter
        except SystemSetting.DoesNotExist:
            form.instance.total_price = 0
        
        messages.success(self.request, 'Transaction recorded successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        context['stations'] = get_user_stations(user_id, user_role)
        context['pumps'] = Pump.objects.filter(station__in=context['stations'])
        return context

# ========== ALERT CRUD ==========
class AlertListView(ListView):
    model = Alert
    template_name = "alerts/list.html"
    context_object_name = "alerts"
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        return Alert.objects.filter(station__in=stations)

class AlertUpdateView(UpdateView):
    model = Alert
    template_name = "alerts/form.html"
    fields = ["status"]
    success_url = reverse_lazy('alert_list')
    pk_url_kwarg = 'alert_id'
    
    def form_valid(self, form):
        messages.success(self.request, 'Alert status updated!')
        return super().form_valid(form)

# ========== SYSTEM SETTINGS CRUD ==========
class SystemSettingListView(ListView):
    model = SystemSetting
    template_name = "settings/list.html"
    context_object_name = "settings"

class SystemSettingCreateView(CreateView):
    model = SystemSetting
    template_name = "settings/form.html"
    fields = ["fuel_type", "price_per_liter"]
    success_url = reverse_lazy('settings_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Fuel type added successfully!')
        return super().form_valid(form)

class SystemSettingUpdateView(UpdateView):
    model = SystemSetting
    template_name = "settings/form.html"
    fields = ["fuel_type", "price_per_liter"]
    success_url = reverse_lazy('settings_list')
    pk_url_kwarg = 'setting_id'
    
    def form_valid(self, form):
        messages.success(self.request, 'Price updated successfully!')
        return super().form_valid(form)

class SystemSettingDeleteView(DeleteView):
    model = SystemSetting
    template_name = "settings/confirm_delete.html"
    success_url = reverse_lazy('settings_list')
    pk_url_kwarg = 'setting_id'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Fuel type deleted successfully!')
        return super().delete(request, *args, **kwargs)