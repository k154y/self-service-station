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
from django.contrib.auth.hashers import check_password



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
            # Use check_password to verify hashed password
            if check_password(password, user.password):
                request.session['user_id'] = user.user_id
                request.session['username'] = user.username
                request.session['role'] = user.role
                request.session['full_name'] = user.full_name
                # Update last_login timestamp
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                messages.success(request, f'Welcome back, {user.full_name}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')
    
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

            # Send welcome email to the new user
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = 'Welcome to Fuel Station Management System'
            message = f'''
Hello {user.full_name},

Welcome to the Fuel Station Management System!

Your account has been successfully created with the following details:

Username: {user.username}
Email: {user.email}
Role: {user.role.title()}

You can now log in to the system using your email and password.

If you have any questions or need assistance, please don't hesitate to contact our support team.

Best regards,
Fuel Station Management Team
            '''
            
            from_email = settings.DEFAULT_FROM_EMAIL
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                # Log the error but don't prevent user creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send welcome email: {str(e)}')
                # Still show success message even if email fails
                messages.warning(request, 'Account created successfully, but we could not send a welcome email. Please check your email settings.')

            messages.success(request, 'Account created successfully!')
            return redirect('landing_page')

    return render(request, 'signup.html')


def forgot_password(request):
    """Forgot password - Step 1: Request reset token"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate password reset token
            reset_token = PasswordResetToken.generate_token(user)
            
            # Send email with reset link
            from django.core.mail import send_mail
            from django.urls import reverse
            from django.conf import settings
            
            reset_url = request.build_absolute_uri(
                reverse('reset_password', args=[reset_token.token])
            )
            
            # Prepare email content
            subject = 'Password Reset Request - Fuel Station'
            message = f'''
Hello {user.full_name},

You requested to reset your password for your Fuel Station account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
Fuel Station Team
            '''
            
            from_email = settings.DEFAULT_FROM_EMAIL or 'noreply@fuelstation.com'
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, f'Password reset link has been sent to {user.email}. Please check your email (including spam folder).')
            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send password reset email: {str(e)}')
                
                # Provide helpful error message
                error_msg = str(e)
                if 'authentication' in error_msg.lower() or 'login' in error_msg.lower():
                    messages.error(request, 'Email authentication failed. Please check your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD settings in settings.py or environment variables.')
                elif 'connection' in error_msg.lower():
                    messages.error(request, 'Could not connect to email server. Please check your EMAIL_HOST and EMAIL_PORT settings.')
                else:
                    messages.error(request, f'Failed to send email: {error_msg}. Please check your email configuration.')
                
                # For development: show the reset URL in a message if email fails
                if settings.DEBUG:
                    messages.info(request, f'DEBUG: Reset URL would be: {reset_url}')
            
            return redirect('landing_page')
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            messages.success(request, 'If an account exists with this email, a password reset link has been sent.')
            return redirect('landing_page')
    
    return render(request, 'forgot_password.html')


def reset_password(request, token):
    """Forgot password - Step 2: Reset password with token"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid():
            messages.error(request, 'This password reset link has expired or has already been used.')
            return redirect('forgot_password')
        
        if request.method == 'POST':
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            # Validate passwords
            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'reset_password.html', {'token': token, 'valid': True})
            
            if len(password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'reset_password.html', {'token': token, 'valid': True})
            
            # Update user password
            from django.contrib.auth.hashers import make_password
            reset_token.user.password = make_password(password)
            reset_token.user.save(update_fields=['password'])
            
            # Mark token as used
            reset_token.used = True
            reset_token.save()
            
            messages.success(request, 'Your password has been reset successfully. Please login with your new password.')
            return redirect('landing_page')
        
        return render(request, 'reset_password.html', {'token': token, 'valid': True})
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('forgot_password')

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
# In service/views.py

class UserProfileView(CustomLoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Fetch the current logged-in user
        user_id = self.request.session.get('user_id')
        user = get_object_or_404(User, user_id=user_id)
        context['profile_user'] = user

        # 2. Fetch Contextual Data based on Role
        if user.role == 'owner':
            # If Owner: Fetch all companies they own
            companies = Company.objects.filter(owner=user)
            context['companies'] = companies
            context['companies_count'] = companies.count()

        elif user.role == 'manager':
            # If Manager: Fetch the station they are assigned to
            # (Note: Using filter().first() prevents crashes if they aren't assigned yet)
            station = Station.objects.filter(manager_id=user).first()
            context['station'] = station
            if station:
                context['company'] = station.company_id
        
        # Admin doesn't need specific extra context (they see everything)
        
        return context

# USER CRUD (Class-Based Views) 
class UserListView(ListView):
    model = User
    template_name = "users/list.html"
    context_object_name = "users"
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        
        if user_role == 'admin':
            # Admin sees all users
            return User.objects.all()
        elif user_role == 'owner':
            # Owner sees only users related to their companies (managers of their stations)
            try:
                owner = User.objects.get(user_id=user_id)
                # Get stations owned by this owner
                owned_stations = Station.objects.filter(company_id__owner=owner)
                # Get managers of those stations
                manager_ids = owned_stations.values_list('manager_id', flat=True).distinct()
                # Include the owner themselves and the managers
                return User.objects.filter(Q(user_id=owner.user_id) | Q(user_id__in=manager_ids))
            except User.DoesNotExist:
                return User.objects.none()
        else:
            # Managers see only themselves
            return User.objects.filter(user_id=user_id)

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
        if current_user_role == "owner":
            if selected_role != "manager":
                messages.error(self.request, "Owners can only create Managers.")
                return redirect("user_list")
            # Prevent owner from creating admin users
            if selected_role == "admin":
                messages.error(self.request, "Owners cannot create admin users.")
                return redirect("user_list")

        user = form.save(commit=False)
        # Hash password if provided
        if 'password' in form.cleaned_data and form.cleaned_data['password']:
            from django.contrib.auth.hashers import make_password
            user.password = make_password(form.cleaned_data['password'])
        user.save()

        # Send welcome email to the newly created user
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Get the creator's name for the email
        try:
            creator = User.objects.get(user_id=self.request.session.get('user_id'))
            creator_name = creator.full_name or creator.username
        except User.DoesNotExist:
            creator_name = "Administrator"
        
        subject = 'Your Account Has Been Created - Fuel Station Management System'
        message = f'''
Hello {user.full_name},

Your account has been successfully created by {creator_name} in the Fuel Station Management System.

Your account details:

Username: {user.username}
Email: {user.email}
Role: {user.role.title()}

You can now log in to the system using your email and password.

If you have any questions or need assistance, please don't hesitate to contact our support team.

Best regards,
Fuel Station Management Team
            '''
        
        from_email = settings.DEFAULT_FROM_EMAIL
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log the error but don't prevent user creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send welcome email to {user.email}: {str(e)}')
            messages.warning(self.request, f'User created successfully, but we could not send a welcome email to {user.email}. Please check your email settings.')

        messages.success(self.request, "User created successfully!")
        return redirect(self.success_url)

class UserUpdateView(UpdateView):
    model = User
    template_name = "users/form.html"
    fields = ["username", "full_name", "email", "password", "role"]
    success_url = reverse_lazy('user_list')
    pk_url_kwarg = 'user_id'
    
    def dispatch(self, request, *args, **kwargs):
        # Get the user being updated
        user_to_update = self.get_object()
        current_user_role = request.session.get('role')
        
        # Prevent non-admins from editing admins
        if user_to_update.role == 'admin' and current_user_role != 'admin':
            messages.error(request, 'You do not have permission to edit admin users.')
            return redirect('user_list')
        
        # Additional checks for owners: can only edit users in their companies
        if current_user_role == 'owner':
            try:
                owner = User.objects.get(user_id=request.session.get('user_id'))
                # Check if the user to update is a manager of the owner's stations
                owned_stations = Station.objects.filter(company_id__owner=owner)
                if user_to_update not in owned_stations.values_list('manager_id', flat=True) and user_to_update != owner:
                    messages.error(request, 'You can only edit users related to your companies.')
                    return redirect('user_list')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('user_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        current_user_role = self.request.session.get('role')
        
        # Owner can only edit managers, not admins
        if current_user_role == 'owner':
            form.fields['role'].choices = [
                ('manager', 'Manager'),
            ]
            # Prevent editing password for owners (optional - you can remove this if needed)
            # form.fields['password'].widget = forms.HiddenInput()
        
        return form
    
    def form_valid(self, form):
        current_user_role = self.request.session.get('role')
        selected_role = form.cleaned_data.get('role')
        
        # Prevent owner from assigning admin role
        if current_user_role == 'owner' and selected_role == 'admin':
            messages.error(self.request, 'Owners cannot assign admin role.')
            return redirect('user_list')
        
        # Hash password if it was changed
        if 'password' in form.cleaned_data and form.cleaned_data['password']:
            from django.contrib.auth.hashers import make_password
            form.instance.password = make_password(form.cleaned_data['password'])
        
        messages.success(self.request, 'User updated successfully!')
        return super().form_valid(form)

class UserDeleteView(DeleteView):
    model = User
    template_name = "users/delete.html"
    success_url = reverse_lazy('user_list')
    pk_url_kwarg = 'user_id'
    
    def dispatch(self, request, *args, **kwargs):
        # Get the user being deleted
        user_to_delete = self.get_object()
        current_user_role = self.request.session.get('role')
        
        # Prevent non-admins from deleting admins
        if user_to_delete.role == 'admin' and current_user_role != 'admin':
            messages.error(self.request, 'You do not have permission to delete admin users.')
            return redirect('user_list')
        
        # Additional checks for owners: can only delete users in their companies
        if current_user_role == 'owner':
            try:
                owner = User.objects.get(user_id=self.request.session.get('user_id'))
                # Check if the user to delete is a manager of the owner's stations
                owned_stations = Station.objects.filter(company_id__owner=owner)
                if user_to_delete.user_id not in owned_stations.values_list('manager_id', flat=True) and user_to_delete != owner:
                    messages.error(self.request, 'You can only delete users related to your companies.')
                    return redirect('user_list')
            except User.DoesNotExist:
                messages.error(self.request, 'User not found.')
                return redirect('user_list')
        
        return super().dispatch(request, *args, **kwargs)
    
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

class StationCreateView(CreateView):
    model = Station
    template_name = "stations/form.html"
    fields = ["company_id", "manager_id", "name", "location", "status"]
    success_url = reverse_lazy('station_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_role = request.session.get('role')
        if user_role not in ['admin', 'owner']:
            messages.error(request, "You do not have permission to create stations.")
            return redirect('station_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        
        if user_role == 'owner':
            try:
                user = User.objects.get(user_id=user_id)
                form.fields['company_id'].queryset = Company.objects.filter(owner=user)
            except User.DoesNotExist:
                form.fields['company_id'].queryset = Company.objects.none()
        # Admin sees all companies by default
        
        return form
    
    def form_valid(self, form):
        company = form.cleaned_data.get('company_id')
        manager = form.cleaned_data.get('manager_id')
        station_name = form.cleaned_data.get('name')
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')

        # 1. Check if station name already exists
        if Station.objects.filter(name=station_name).exists():
            messages.error(self.request, f'A station with the name "{station_name}" already exists. Please use a unique name.')
            return self.form_invalid(form)

        # 2. Check if manager is an owner trying to manage a station outside their company
        if manager and manager.role == 'owner':
            try:
                manager_user = User.objects.get(user_id=manager.user_id)
                # Owner can only manage stations for companies they own
                if manager_user != company.owner:
                    messages.error(
                        self.request,
                        f'Owner "{manager.username}" can only manage stations for companies they own. They do not own "{company.name}".'
                    )
                    return self.form_invalid(form)
            except User.DoesNotExist:
                messages.error(self.request, 'Manager user not found.')
                return self.form_invalid(form)

        # 3. Check if manager (manager role) already manages stations in a different company
        if manager and manager.role == 'manager':
            existing_stations = Station.objects.filter(manager_id=manager).exclude(pk=self.object.pk if self.object else None)
            
            if existing_stations.exists():
                existing_company = existing_stations.first().company_id
                
                if existing_company != company:
                    messages.error(
                        self.request,
                        f'Manager "{manager.username}" already manages a station for company "{existing_company.name}". They cannot be assigned to a station under "{company.name}".'
                    )
                    return self.form_invalid(form)

        messages.success(self.request, 'Station created successfully!')
        return super().form_valid(form)

class StationUpdateView(UpdateView):
    model = Station
    template_name = "stations/form.html"
    fields = ["company_id", "manager_id", "name", "location", "status"]
    success_url = reverse_lazy('station_list')
    pk_url_kwarg = 'station_id'
    
    def dispatch(self, request, *args, **kwargs):
        user_role = request.session.get('role')
        if user_role not in ['admin', 'owner']:
            messages.error(request, "You do not have permission to update stations.")
            return redirect('station_list')
        
        # Check if the station belongs to the user's companies
        station = self.get_object()
        user_id = request.session.get('user_id')
        if user_role == 'owner':
            try:
                user = User.objects.get(user_id=user_id)
                if station.company_id.owner != user:
                    messages.error(request, "You can only update stations in your companies.")
                    return redirect('station_list')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('station_list')
        # Admin can update any
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        
        if user_role == 'owner':
            try:
                user = User.objects.get(user_id=user_id)
                # Owner can only select their own companies
                form.fields['company_id'].queryset = Company.objects.filter(owner=user)
                # Owner can only select managers they created (under their companies)
                owned_stations = Station.objects.filter(company_id__owner=user)
                manager_ids = owned_stations.values_list('manager_id', flat=True).distinct()
                # Only show managers (not admins) that belong to owner's companies
                form.fields['manager_id'].queryset = User.objects.filter(
                    user_id__in=manager_ids, 
                    role='manager'
                )
            except User.DoesNotExist:
                form.fields['company_id'].queryset = Company.objects.none()
                form.fields['manager_id'].queryset = User.objects.none()
        # Admin sees all companies and all users by default
        
        return form
    
    def form_valid(self, form):
        company = form.cleaned_data.get('company_id')
        manager = form.cleaned_data.get('manager_id')
        station_name = form.cleaned_data.get('name')
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')

        # 1. Check if station name already exists (exclude current station)
        if Station.objects.filter(name=station_name).exclude(pk=self.object.pk).exists():
            messages.error(self.request, f'A station with the name "{station_name}" already exists. Please use a unique name.')
            return self.form_invalid(form)

        # 2. Check if manager is an owner trying to manage a station outside their company
        if manager and manager.role == 'owner':
            try:
                manager_user = User.objects.get(user_id=manager.user_id)
                # Owner can only manage stations for companies they own
                if manager_user != company.owner:
                    messages.error(
                        self.request,
                        f'Owner "{manager.username}" can only manage stations for companies they own. They do not own "{company.name}".'
                    )
                    return self.form_invalid(form)
            except User.DoesNotExist:
                messages.error(self.request, 'Manager user not found.')
                return self.form_invalid(form)

        # 3. Check if manager (manager role) already manages stations in a different company
        if manager and manager.role == 'manager':
            existing_stations = Station.objects.filter(manager_id=manager).exclude(pk=self.object.pk)
            
            if existing_stations.exists():
                existing_company = existing_stations.first().company_id
                
                if existing_company != company:
                    messages.error(
                        self.request,
                        f'Manager "{manager.username}" already manages a station for company "{existing_company.name}". They cannot be assigned to a station under "{company.name}".'
                    )
                    return self.form_invalid(form)

        messages.success(self.request, 'Station updated successfully!')
        return super().form_valid(form)

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

class PumpCreateView(CustomLoginRequiredMixin, CreateView):
    model = Pump
    template_name = "pumps/form.html"
    fields = ["station", "pump_number", "fuel_type", "status", "flow_rate"]
    success_url = reverse_lazy('pump_list')

    def dispatch(self, request, *args, **kwargs):
        # Ensure user has permission to create pumps
        user_role = request.session.get('role')
        if user_role not in ['admin', 'owner']:
            messages.error(request, "You do not have permission to create pumps.")
            return redirect('pump_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        form.fields['station'].queryset = stations
        return form

    def form_valid(self, form):
        # Additional check: ensure the station belongs to the user (for owner)
        user_role = self.request.session.get('role')
        if user_role == 'owner':
            station = form.cleaned_data.get('station')
            user_id = self.request.session.get('user_id')
            try:
                user = User.objects.get(user_id=user_id)
                if station.company_id.owner != user:
                    messages.error(self.request, "You can only add pumps to stations in your companies.")
                    return self.form_invalid(form)
            except User.DoesNotExist:
                messages.error(self.request, "User not found.")
                return self.form_invalid(form)
        messages.success(self.request, 'Pump created successfully!')
        return super().form_valid(form)

class PumpUpdateView(CustomLoginRequiredMixin, UpdateView):
    model = Pump
    template_name = "pumps/form.html"
    fields = ["station", "pump_number", "fuel_type", "status", "flow_rate"]
    success_url = reverse_lazy('pump_list')
    pk_url_kwarg = 'pump_id'

    def dispatch(self, request, *args, **kwargs):
        # Check if user can access this pump
        pump = self.get_object()
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        if pump.station not in stations:
            messages.error(self.request, "You do not have permission to edit this pump.")
            return redirect('pump_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        form.fields['station'].queryset = stations
        return form

    def form_valid(self, form):
        # Additional check for owner: ensure station belongs to them
        user_role = self.request.session.get('role')
        if user_role == 'owner':
            station = form.cleaned_data.get('station')
            user_id = self.request.session.get('user_id')
            try:
                user = User.objects.get(user_id=user_id)
                if station.company_id.owner != user:
                    messages.error(self.request, "You can only edit pumps for stations in your companies.")
                    return self.form_invalid(form)
            except User.DoesNotExist:
                messages.error(self.request, "User not found.")
                return self.form_invalid(form)
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
            if item.capacity and item.capacity > 0:
                item.percentage = (item.quantity / item.capacity) * 100
            else:
                item.percentage = 0
            
            # Status based on percentage: Above 25% = Good, 25% and below = Low
            if item.percentage > 25:
                item.status = 'Good'
            else:
                item.status = 'Low'
        
        return inventory


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
            
            # Status based on percentage: Above 25% = Good, 25% and below = Low
            if item.percentage > 25:
                item.status = 'Good'
            else:
                item.status = 'Low'
            
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
        inventory = form.save(commit=False)
        
        # 1. Validate quantity doesn't exceed capacity
        if inventory.quantity > inventory.capacity:
            messages.error(self.request, f'Quantity ({inventory.quantity}L) cannot exceed capacity ({inventory.capacity}L).')
            return self.form_invalid(form)
        
        # 2. Get old quantity before saving
        old_quantity = self.get_object().quantity
        new_quantity = inventory.quantity
        
        # Save the inventory first
        inventory.save()
        
        # 3. Handle alerts based on quantity vs min_threshold
        if new_quantity <= inventory.min_threshold:
            # Quantity is at or below threshold - create or update alert
            alert, created = Alert.objects.get_or_create(
                inventory_id=inventory,
                status='pending',
                defaults={
                    'station': inventory.station_id,
                    'type': 'inventory',
                    'description': f'Low inventory alert: {inventory.fuel_type} at {inventory.station_id.name} is at {new_quantity}L, which is below the minimum threshold of {inventory.min_threshold}L.',
                }
            )
            if not created:
                # Update existing alert if quantity changed
                alert.description = f'Low inventory alert: {inventory.fuel_type} at {inventory.station_id.name} is at {new_quantity}L, which is below the minimum threshold of {inventory.min_threshold}L.'
                alert.status = 'pending'  # Reset to pending if it was resolved
                alert.save()
        else:
            # Quantity is above threshold - resolve any existing alerts for this inventory
            Alert.objects.filter(
                inventory_id=inventory,
                type='inventory',
                status='pending'
            ).update(status='resolved')
        
        messages.success(self.request, 'Inventory updated successfully!')
        return redirect(self.success_url)

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


# ========== USER PROFILE VIEW ==========
class UserProfileView(UpdateView):
    model = User
    template_name = "users/profile.html"
    fields = ["username", "full_name", "email"]
    success_url = reverse_lazy('dashboard')
    context_object_name = 'profile_user'
    
    def get_object(self):
        # Get the current logged-in user
        user_id = self.request.session.get('user_id')
        return get_object_or_404(User, user_id=user_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        if user.role == 'owner':
            companies = Company.objects.filter(owner=user)
            context['companies'] = companies
            context['companies_count'] = companies.count()
        elif user.role == 'manager':
            # Assuming manager has a station
            station = Station.objects.filter(manager_id=user).first()
            if station:
                context['station'] = station
                context['company'] = station.company_id
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)