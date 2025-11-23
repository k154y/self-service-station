# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, Station, Pump, Inventory, Transaction, Alert

def landing_page(request):
    """Landing page - Login screen"""
    # if request.user.is_authenticated:
    #     return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            if user.password == password:  # In real app, use proper password hashing
                # Simulate login (you should use Django's authentication system)
                request.session['user_id'] = user.user_id
                request.session['username'] = user.username
                request.session['role'] = user.role
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials')
        except User.DoesNotExist:
            messages.error(request, 'User does not exist')
    
    return render(request, 'landing.html')

def signup_page(request):
    """Sign up page"""
    if request.method == 'POST':
        # Handle signup logic here
        pass
    return render(request, 'signup.html')

def forgot_password(request):
    """Forgot password page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        # Handle password reset logic here
        messages.success(request, 'Please check your email for a confirmation link')
        return redirect('landing_page')
    
    return render(request, 'forgot_password.html')

@login_required
def dashboard(request):
    """Main dashboard after login"""
    # Get user from session (in real app, use request.user)
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('landing_page')
    
    try:
        user = User.objects.get(user_id=user_id)
        
        # Get stations based on user role
        if user.role == 'admin':
            stations = Station.objects.all()
        elif user.role == 'owner':
            stations = Station.objects.filter(company_id__owner=user)
        elif user.role == 'manager':
            stations = Station.objects.filter(manager_id=user)
        else:
            stations = Station.objects.none()
        
        # Get pumps and their status
        pumps = Pump.objects.filter(station__in=stations)
        active_pumps = pumps.filter(status='active').count()
        offline_pumps = pumps.filter(status='offline').count()
        
        # Get inventory data
        inventory = Inventory.objects.filter(station_id__in=stations)
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(station_id__in=stations).order_by('-transaction_time')[:5]
        
        # Get today's revenue
        from django.utils import timezone
        from django.db.models import Sum
        today = timezone.now().date()
        today_revenue = Transaction.objects.filter(
            station_id__in=stations,
            transaction_time__date=today
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        context = {
            'user': user,
            'stations': stations,
            'pumps': pumps,
            'active_pumps_count': active_pumps,
            'offline_pumps_count': offline_pumps,
            'inventory': inventory,
            'recent_transactions': recent_transactions,
            'today_revenue': today_revenue,
        }
        
        return render(request, 'dashboard.html', context)
        
    except User.DoesNotExist:
        return redirect('landing_page')

def user_logout(request):
    """Logout user"""
    logout(request)
    request.session.flush()
    return redirect('landing_page')