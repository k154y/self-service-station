from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView,TemplateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.contrib.auth.mixins import UserPassesTestMixin,LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from .models import *
from django.http import HttpResponseForbidden,JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db import transaction



class CustomLoginRequiredMixin:
    """
    Custom mixin to check if the user is logged in via session.
    Replaces Django's LoginRequiredMixin for your custom auth system.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, "Please log in to access this page.")
            return redirect('landing_page')
        return super().dispatch(request, *args, **kwargs)

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

# def signup_page(request):
#     """Sign up page"""
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         full_name = request.POST.get('full_name')
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#         role = request.POST.get('role', 'manager')
        
#         if User.objects.filter(username=username).exists():
#             messages.error(request, 'Username already exists')
#         elif User.objects.filter(email=email).exists():
#             messages.error(request, 'Email already exists')
#         else:
#             user = User.objects.create(
#                 username=username,
#                 full_name=full_name,
#                 email=email,
#                 password=password,
#                 role=role
#             )
#             messages.success(request, 'Account created successfully! Please login.')
#             return redirect('landing_page')
    
#     return render(request, 'signup.html')
from django.contrib.auth.hashers import make_password

def signup_page(request):
    """Sign up page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'manager')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')

        # Check if email already exists
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')

        else:
            # Create a user with a hashed password
            user = User.objects.create(
                username=username,
                full_name=full_name,
                email=email,
                password=make_password(password),   # <-- HASHED PASSWORD
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

    if user_role == 'admin':
        # Admin sees all stations across all companies
        return Station.objects.all()

    elif user_role == 'owner':
        # Owner sees stations associated with companies they own
        return Station.objects.filter(company_id__owner=user)

    elif user_role == 'manager':
        # Manager sees stations they are assigned to manage
        return Station.objects.filter(manager_id=user)

    return Station.objects.none()

# USER CRUD (Class-Based Views) 
class UserListView(ListView):
    model = User
    template_name = "users/list.html"
    context_object_name = "users"

# class UserCreateView(CreateView):
#     model = User
#     template_name = "users/form.html"
#     fields = ["username", "full_name", "email", "password", "role"]
#     success_url = reverse_lazy('user_list')
    
#     def form_valid(self, form):
#         messages.success(self.request, 'User created successfully!')
#         return super().form_valid(form)


class UserCreateView(CustomLoginRequiredMixin, CreateView):
    model = User
    template_name = "users/form.html"
    fields = ["username", "full_name", "email", "password", "role"]
    success_url = reverse_lazy('user_list')

    # 1. Custom Permission Check
    def dispatch(self, request, *args, **kwargs):
        # First, ensure logged in (handled by Mixin, but we need the user object)
        if not request.session.get('user_id'):
            return redirect('landing_page')

        # Fetch the current user object from your custom model
        try:
            current_user = User.objects.get(user_id=request.session.get('user_id'))
        except User.DoesNotExist:
            return redirect('landing_page')

        # Check permissions
        if current_user.role not in ['admin', 'owner']:
            messages.error(request, "You are not allowed to create users.")
            return redirect('user_list')

        return super().dispatch(request, *args, **kwargs)

    # 2. Filter Roles in Form
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # We need to fetch the user again or store it in the request
        current_user_role = self.request.session.get('role')

        if current_user_role == "owner":
            # Owner can ONLY create managers
            form.fields["role"].choices = [
                ('manager', 'Manager'),
            ]
        # Admin keeps all choices by default
        return form

    # 3. Handle Creation
    def form_valid(self, form):
        current_user_role = self.request.session.get('role')
        selected_role = form.cleaned_data['role']

        # Double check permission on submit
        if current_user_role == "owner" and selected_role != "manager":
            messages.error(self.request, "Owners can only create Managers.")
            return redirect("user_list")

        user = form.save(commit=False)
        # Note: Since you are using a custom model, ensure your save logic 
        # handles password hashing if you aren't using Django's AbstractBaseUser.
        # If storing plain text (not recommended): user.password = form.cleaned_data['password']
        user.save()

        messages.success(self.request, "User created successfully!")
        return redirect(self.success_url)

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
    template_name = "users/delete.html"
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
    template_name = "companies/delete.html"
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

# ... (inside views.py)

class StationCreateView(CreateView):
    model = Station
    template_name = "stations/form.html"
    fields = ["company_id", "manager_id", "name", "location", "status"]
    success_url = reverse_lazy('station_list')
    
    def form_valid(self, form):
        manager = form.cleaned_data.get('manager_id')
        new_company = form.cleaned_data.get('company_id')

        if manager and manager.role == 'manager':
            # Check if this manager already manages stations
            existing_stations = Station.objects.filter(manager_id=manager).exclude(pk=self.object.pk if self.object else None)
            
            if existing_stations.exists():
                # Get the company of the manager's existing station(s)
                # We can assume all existing stations for this manager are under the same company
                # based on the model's design intention (one manager per station)
                existing_company = existing_stations.first().company_id
                
                if existing_company != new_company:
                    # BLOCK THE ACTION
                    messages.error(
                        self.request, 
                        f'Manager {manager.username} already manages a station for company "{existing_company.name}". They cannot be assigned to a station under "{new_company.name}".'
                    )
                    return self.form_invalid(form) # Return to the form with error

        messages.success(self.request, 'Station created successfully!')
        return super().form_valid(form) # Save the form if validation passes
    
# ... (inside views.py)

class StationUpdateView(UpdateView):
    model = Station
    template_name = "stations/form.html"
    fields = ["company_id", "manager_id", "name", "location", "status"]
    success_url = reverse_lazy('station_list')
    pk_url_kwarg = 'station_id'
    
    def form_valid(self, form):
        manager = form.cleaned_data.get('manager_id')
        updated_company = form.cleaned_data.get('company_id')

        if manager and manager.role == 'manager':
            # Check if this manager already manages stations
            # IMPORTANT: Exclude the *current* station object being updated (self.object)
            existing_stations = Station.objects.filter(manager_id=manager).exclude(pk=self.object.pk)
            
            if existing_stations.exists():
                existing_company = existing_stations.first().company_id
                
                if existing_company != updated_company:
                    # BLOCK THE ACTION
                    messages.error(
                        self.request, 
                        f'Manager {manager.username} already manages a station for company "{existing_company.name}". They cannot be assigned to a station under "{updated_company.name}".'
                    )
                    return self.form_invalid(form) # Return to the form with error

        messages.success(self.request, 'Station updated successfully!')
        return super().form_valid(form) # Save the form if validation passes

class StationDeleteView(DeleteView):
    model = Station
    template_name = "stations/delete.html"
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
class AdminPumpListView(PumpListView):
    """
    Dedicated view for the Admin Pump Management Tool (Table format).
    Inherits queryset logic but overrides the template.
    """
    template_name = "pumps/admin_list.html" # <-- Table View Template
    
    # Override get_context_data to ensure unnecessary card counts aren't calculated
    def get_context_data(self, **kwargs):
        # We don't need status counts in the table view, so skip the logic from the parent view if it exists.
        context = super(PumpListView, self).get_context_data(**kwargs)
        # We still need the pumps queryset which is handled by get_queryset
        return context

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
        context['can_edit'] = user_role in ['admin', 'owner']
        context['user_role'] = user_role
        return context


class InventoryUpdateView(InventoryAccessMixin, UpdateView):
    model = Inventory
    template_name = "inventory/update.html" # Renamed to match my previous suggestion
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
        if user_role == 'admin':
            return True
            
        # Managers are not allowed to update
        if user_role == 'manager':
            return False 
        
        # Owner check: Must own the company associated with the station
        if user_role == 'owner':
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
    paginate_by = 15  # Set default pagination

    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        
        # 1. Base Queryset (Role-Based Filtering)
        # Reusing the existing user station logic for filtering
        authorized_stations = get_user_stations(user_id, user_role)
        queryset = Transaction.objects.filter(station_id__in=authorized_stations).select_related('station_id', 'pump_id')

        # 2. Applying Advanced Filters from GET parameters
        
        # --- Time Filter (duration) ---
        duration = self.request.GET.get('duration', 'all')
        if duration == '24hrs':
            time_cutoff = timezone.now() - timedelta(hours=24)
            queryset = queryset.filter(transaction_time__gte=time_cutoff)
        elif duration == 'week':
            time_cutoff = timezone.now() - timedelta(weeks=1)
            queryset = queryset.filter(transaction_time__gte=time_cutoff)
        elif duration == 'month':
            time_cutoff = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(transaction_time__gte=time_cutoff)
        # 'all' (default) needs no filter
        
        # --- Payment Method Filter ---
        payment_method = self.request.GET.get('payment_method')
        if payment_method and payment_method != 'all':
            queryset = queryset.filter(payment_method=payment_method)

        # --- Station Filter (Admin/Owner Specific) ---
        # Note: Manager is already restricted by 'authorized_stations'
        selected_station_id = self.request.GET.get('station_id')
        if user_role in ['Admin', 'Owner'] and selected_station_id and selected_station_id != 'all':
            # This filter is already somewhat redundant if authorized_stations is used, 
            # but it is necessary if the user explicitly filters down the list.
            queryset = queryset.filter(station_id=selected_station_id)

        # --- Search Filter (Car Plate, Fuel Type, Payment Method ID) ---
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(fuel_type__icontains=search_query) |
                Q(payment_method__icontains=search_query) |
                Q(car_plate__icontains=search_query) |
                Q(transaction_id__icontains=search_query) # Search by ID
            )
        
        # Default ordering: most recent first
        return queryset.order_by('-transaction_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations_for_stats = get_user_stations(user_id, user_role)
        
        # 1. Pass Filter Options and Current Selections
        context['user_role'] = user_role
        context['duration_options'] = [('all', 'All Time'), ('24hrs', 'Last 24 Hours'), ('week', 'Last Week'), ('month', 'Last Month')]
        context['payment_methods'] = Transaction.PAYMENT_METHODS
        
        # Stations available for filtering (Only applicable for Admin/Owner in the template)
        context['filterable_stations'] = Station.objects.filter(pk__in=[s.pk for s in stations_for_stats]).order_by('name')
        
        # Current filter values for dropdown persistence
        context['current_duration'] = self.request.GET.get('duration', 'all')
        context['current_payment_method'] = self.request.GET.get('payment_method', 'all')
        context['current_station_id'] = self.request.GET.get('station_id', 'all')
        context['search_query'] = self.request.GET.get('search', '')

        # 2. Summary Totals (Totals are calculated BEFORE pagination, but AFTER role-based filtering)
        all_transactions_for_role = self.model.objects.filter(station_id__in=stations_for_stats)
        
        today = timezone.now().date()
        today_totals = all_transactions_for_role.filter(transaction_time__date=today).aggregate(
            total_revenue=Sum('total_price'),
            total_petrol_dispensed=Sum('quantity', filter=Q(fuel_type='Petrol')),
            total_diesel_dispensed=Sum('quantity', filter=Q(fuel_type='Diesel')),
        )
        
        context['today_revenue'] = today_totals['total_revenue'] or 0
        context['total_petrol_dispensed'] = today_totals['total_petrol_dispensed'] or 0
        context['total_diesel_dispensed'] = today_totals['total_diesel_dispensed'] or 0
        context['total_transactions_count'] = all_transactions_for_role.count() # Count of all available transactions (pre-filter)
        
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
    paginate_by = 20 # Standard pagination size

    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        
        # 1. Base Queryset (Role-Based Access)
        # Filters alerts down to stations the user is authorized to see
        authorized_stations = get_user_stations(user_id, user_role)
        queryset = Alert.objects.filter(station__in=authorized_stations).select_related('station', 'pump_id', 'inventory_id')

        # 2. Applying Filters from GET parameters
        
        # --- Status Filter ---
        status_filter = self.request.GET.get('status', 'pending') # Default to pending
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        # --- Type Filter ---
        type_filter = self.request.GET.get('type')
        if type_filter and type_filter != 'all':
            queryset = queryset.filter(type=type_filter)
            
        # --- Company Filter (Admin only) ---
        selected_company_id = self.request.GET.get('company_id')
        if user_role == 'admin' and selected_company_id and selected_company_id != 'all':
            queryset = queryset.filter(station__company_id=selected_company_id)
            
        # --- Station Filter (Admin/Owner control) ---
        selected_station_id = self.request.GET.get('station_id')
        if user_role in ['admin', 'owner'] and selected_station_id and selected_station_id != 'all':
            queryset = queryset.filter(station__pk=selected_station_id)

        # Default ordering: most recent first
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        
        # Determine all stations the user *could* filter by (used for summary stats and dropdowns)
        authorized_stations = get_user_stations(user_id, user_role)
        
        context['user_role'] = user_role
        
        # Filter Options
        context['status_options'] = Alert.status_choices
        context['type_options'] = Alert.type_choices
        
        # Get companies/stations for dropdown filtering
        if user_role == 'admin':
             # Admin sees all companies
            context['filterable_companies'] = Company.objects.all().order_by('name')
            context['filterable_stations'] = Station.objects.all().order_by('name')
        elif user_role == 'owner':
            # Owner sees their companies' stations
            try:
                owner_user = get_object_or_404(User, user_id=user_id)
                owner_companies = Company.objects.filter(owner=owner_user)
                context['filterable_companies'] = owner_companies
                context['filterable_stations'] = Station.objects.filter(company_id__in=owner_companies).order_by('name')
            except:
                context['filterable_companies'] = Company.objects.none()
                context['filterable_stations'] = Station.objects.none()
        else: # Manager sees only their assigned stations (covered by base queryset filtering)
             context['filterable_stations'] = Station.objects.filter(pk__in=[s.pk for s in authorized_stations]).order_by('name')
        
        # Current Filter Values for dropdown persistence
        context['current_status'] = self.request.GET.get('status', 'pending')
        context['current_type'] = self.request.GET.get('type', 'all')
        context['current_company_id'] = self.request.GET.get('company_id', 'all')
        context['current_station_id'] = self.request.GET.get('station_id', 'all')
        
        # Counts for status cards (calculated over all authorized alerts)
        all_alerts_for_role = Alert.objects.filter(station__in=authorized_stations)
        context['pending_count'] = all_alerts_for_role.filter(status='pending').count()
        context['resolved_count'] = all_alerts_for_role.filter(status='resolved').count()
        context['total_alerts'] = all_alerts_for_role.count()

        return context

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
    from django.views.generic import TemplateView


class SettingsView(TemplateView):
    template_name = "settings/list.html"
    
    def get_user_data(self):
        """Helper to get user role and data for context."""
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        user = None
        
        if user_id:
            try:
                # Assuming User model is what you provided
                user = User.objects.get(user_id=user_id) 
            except User.DoesNotExist:
                pass
                
        return user, user_role

    def get_context_data(self, **kwargs):
     context = super().get_context_data(**kwargs)
     user, user_role = self.get_user_data()

     # --- DEBUG LINES START ---
     print(f"DEBUG: Current User ID: {self.request.session.get('user_id')}")
     print(f"DEBUG: Role from session: {user_role}")

     # NOTE: You need to import Company model at the top of the file
     # from .models import Company 

     if user_role == 'admin':
        all_companies_qs = Company.objects.all().order_by('name')
        print(f"DEBUG: Admin found {all_companies_qs.count()} companies.")
        context['all_companies'] = all_companies_qs
     elif user_role == 'owner':
        owner_companies_qs = Company.objects.filter(owner=user).order_by('name')
        print(f"DEBUG: Owner found {owner_companies_qs.count()} companies.")
        context['owner_companies'] = owner_companies_qs

    # --- DEBUG LINES END ---

     context['user_role'] = user_role
    # ... rest of your code ...
     return context
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user, user_role = self.get_user_data()
        action = request.POST.get('action')

        if action == 'update_pricing':
            fuel_type = request.POST.get('fuel_type')
            new_price = request.POST.get('price_per_liter')
            
            # --- Role-Based Price Update Logic ---
            if user_role == 'admin':
                # Admin can set price globally for a fuel type
                try:
                    setting = SystemSetting.objects.get(fuel_type=fuel_type)
                    setting.price_per_liter = new_price
                    setting.update_prices(user_role) # Global update
                    messages.success(request, f'Global price for {fuel_type} updated to {new_price} RWF.')
                except SystemSetting.DoesNotExist:
                    messages.error(request, 'Fuel type not found.')
                    
            elif user_role == 'owner':
                # Owner can set price for their specific company/stations
                company_id = request.POST.get('company_id')
                try:
                    # 1. Update the SystemSetting price (acts as the master price)
                    setting = SystemSetting.objects.get(fuel_type=fuel_type)
                    setting.price_per_liter = new_price
                    setting.update_prices(user_role, company_id) # Company-specific Inventory update
                    messages.success(request, f'Company price for {fuel_type} updated to {new_price} RWF.')
                except SystemSetting.DoesNotExist:
                    messages.error(request, 'Fuel type not found.')
                    
            else:
                messages.error(request, 'You do not have permission to change pricing.')

        # Future actions like 'add_company', 'add_manager', 'add_station' would go here...

        return redirect(reverse_lazy('settings_list')) # Redirect back to the settings page