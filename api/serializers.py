# C:\Users\k.yves\Desktop\self_service_station\api\serializers.py

from rest_framework import serializers
from service.models import User, Company, Station, Pump, Inventory, Transaction, Alert, SystemSetting

# --- User Serializers ---
class UserSerializer(serializers.ModelSerializer):
    """Used for reading user data (excludes password)."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['user_id', 'username', 'full_name', 'email', 'role', 'role_display', 'created_at']
        read_only_fields = ['user_id', 'created_at']

class UserCreateSerializer(serializers.ModelSerializer):
    """Used for creating users. Handles password hashing."""
    class Meta:
        model = User
        fields = ['user_id', 'username', 'full_name', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Hash password using Django's default hasher or your custom logic
        from django.contrib.auth.hashers import make_password
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

# --- Company Serializer ---
class CompanySerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Company
        fields = ['company', 'name', 'owner', 'owner_username', 'created_at']
        read_only_fields = ['company', 'created_at']

# --- Station Serializer ---
class StationSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company_id.name', read_only=True)
    manager_name = serializers.CharField(source='manager_id.full_name', read_only=True)
    
    class Meta:
        model = Station
        fields = ['station_id', 'company_id', 'company_name', 'manager_id', 'manager_name', 'name', 'location', 'status', 'created_at']
        read_only_fields = ['station_id', 'created_at']

# --- Pump Serializer ---
class PumpSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Pump
        fields = '__all__'

# --- Inventory Serializer ---
class InventorySerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station_id.name', read_only=True)
    
    class Meta:
        model = Inventory
        fields = '__all__'
        read_only_fields = ['inventory_id', 'updated_at', 'capacity', 'fuel_type', 'station_id']

# --- Transaction Serializer ---
class TransactionCreateSerializer(serializers.ModelSerializer):
    """Used for creating transactions. Price is calculated server-side."""
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'station_id', 'user_id', 'pump_id', 
            'fuel_type', 'quantity', 'total_price', 'payment_method', 
            'car_plate', 'transaction_time'
        ]
        # total_price is read-only because the API calculates it based on SystemSettings
        read_only_fields = ['transaction_id', 'transaction_time', 'total_price']

class TransactionSerializer(serializers.ModelSerializer):
    """Used for listing transactions."""
    station_name = serializers.CharField(source='station_id.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'

# --- Alert Serializer ---
class AlertSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ['alert_id', 'created_at']

# --- System Setting Serializer (NEW) ---
class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['setting_id', 'fuel_type', 'price_per_liter', 'updated_at']
        read_only_fields = ['setting_id', 'updated_at']