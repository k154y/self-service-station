from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import secrets



# User Manager
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            from django.contrib.auth.hashers import make_password
            user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)


# Users
class User(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('manager', 'Manager'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='manager')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Required fields for AbstractBaseUser
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']
    
    objects = UserManager()

    def __str__(self):
        return self.username or self.email
    
    def get_full_name(self):
        return self.full_name
    
    def get_short_name(self):
        return self.username
    
    @property
    def is_staff(self):
        return self.role == 'admin'
    
    @property
    def is_superuser(self):
        return self.role == 'admin'
    
    def has_perm(self, perm, obj=None):
        return self.role == 'admin'
    
    def has_module_perms(self, app_label):
        return self.role == 'admin'



# Companies

class Company(models.Model):
    company= models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



# Stations

class Station(models.Model):
    station_id = models.AutoField(primary_key=True)
    company_id= models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stations')
    manager_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_stations')
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name


# Pumps (Weak Entity)

class Pump(models.Model):
    pump_id = models.AutoField(primary_key=True)
    station= models.ForeignKey(Station, on_delete=models.CASCADE, related_name='pumps')
    pump_number = models.IntegerField()
    fuel_type = models.CharField(max_length=50)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('offline', 'Offline'),
        
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    flow_rate = models.FloatField(null=True, blank=True)
    

    class Meta:
        unique_together = ('station', 'pump_number')

    def __str__(self):
        return f"Pump {self.pump_number} - {self.station.name}"



# System Settings

class SystemSetting(models.Model):
    setting_id = models.AutoField(primary_key=True)
    fuel_type = models.CharField(max_length=50)
    price_per_liter = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def update_prices(self, user_role, company_id=None):
        """Updates prices in SystemSetting and relevant Inventory models."""
        
        # 1. Update the SystemSetting (Global/Company Price)
        self.save() 
        
        # 2. Update Inventory prices (Synchronize)
        
        # Admin: Updates Inventory for ALL stations/companies with this fuel_type
        if user_role == 'admin':
            Inventory.objects.filter(fuel_type=self.fuel_type).update(unit_price=self.price_per_liter)
            
        # Owner: Updates Inventory only for stations under their company(ies)
        elif user_role == 'owner' and company_id:
            Inventory.objects.filter(
                fuel_type=self.fuel_type, 
                station_id__company_id=company_id
            ).update(unit_price=self.price_per_liter)
            
        # Manager/Other: No price setting privilege

    def __str__(self):
        return f"{self.fuel_type}"



# Inventory (Weak Entity)
# class Inventory(models.Model):
#     inventory_id = models.AutoField(primary_key=True)
#     station_id= models.ForeignKey(Station, on_delete=models.CASCADE, related_name='inventory')
#     fuel_type = models.CharField(max_length=50)
#     quantity = models.FloatField()
#     capacity = models.FloatField()
#     min_threshold = models.FloatField()
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         unique_together = ('station_id', 'fuel_type')

#     def __str__(self):
#         return f"{self.station.name} - {self.fuel_type}"

class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    station_id= models.ForeignKey(Station, on_delete=models.CASCADE, related_name='inventory')
    fuel_type = models.CharField(max_length=50)
    quantity = models.FloatField()
    capacity = models.FloatField()
    min_threshold = models.FloatField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('station_id', 'fuel_type')

    def __str__(self):
        # FIX APPLIED: Changed self.station.name to self.station_id.name
        return f"{self.station_id.name} - {self.fuel_type}"

# Transactions

class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    station_id= models.ForeignKey(Station, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    pump_id = models.ForeignKey(Pump, on_delete=models.CASCADE)
    fuel_type = models.CharField(max_length=50)
    quantity = models.FloatField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('momo', 'Mobile Money'),
        ('card', 'Card'),
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    car_plate = models.CharField(max_length=20, blank=True, null=True)
    transaction_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.transaction_id}"



# Alerts

class Alert(models.Model):
    alert_id = models.AutoField(primary_key=True)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    type_choices = [
        ('security', 'Security'),
        ('maintenance', 'Maintenance'),
        ('inventory', 'Inventory'),
        ('system', 'System'),
    ]
    type = models.CharField(max_length=20, choices=type_choices)
    description = models.TextField()
    pump_id = models.ForeignKey(Pump, on_delete=models.SET_NULL, null=True, blank=True)
    inventory_id = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status_choices = [
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='pending')

    def __str__(self):
        return f"Alert {self.alert_id} - {self.type}"


# Password Reset Token
class PasswordResetToken(models.Model):
    token = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    @classmethod
    def generate_token(cls, user):
        """Generate a new password reset token for a user"""
        # Delete any existing unused tokens for this user
        cls.objects.filter(user=user, used=False).delete()
        
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)  # Token valid for 24 hours
        
        return cls.objects.create(
            token=token,
            user=user,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """Check if token is valid and not expired"""
        return not self.used and timezone.now() < self.expires_at
