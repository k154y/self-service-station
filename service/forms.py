# forms.py
from django import forms
from .models import *

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password', 'role']
        widgets = {
            'password': forms.PasswordInput(),
        }

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'owner']

class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['company_id', 'manager_id', 'name', 'location', 'status']

class PumpForm(forms.ModelForm):
    class Meta:
        model = Pump
        fields = ['station', 'pump_number', 'fuel_type', 'status', 'flow_rate']

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['station_id', 'fuel_type', 'quantity', 'capacity', 'min_threshold', 'unit_price']

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['station_id', 'pump_id', 'fuel_type', 'quantity', 'total_price', 'payment_method', 'car_plate']

class SystemSettingForm(forms.ModelForm):
    class Meta:
        model = SystemSetting
        fields = ['fuel_type', 'price_per_liter']