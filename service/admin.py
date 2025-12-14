from django.contrib import admin
from .models import User, Company, Station, Pump, SystemSetting, Inventory, Transaction, Alert, PasswordResetToken


# User Admin

class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'full_name', 'email', 'role', 'created_at', 'last_login')

admin.site.register(User, UserAdmin)



# Company Admin

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company', 'name', 'owner', 'created_at')

admin.site.register(Company, CompanyAdmin)



# Station Admin

class StationAdmin(admin.ModelAdmin):
    list_display = ('station_id', 'name', 'company_id', 'manager_id', 'location', 'status', 'created_at')

admin.site.register(Station, StationAdmin)



# Pump Admin

class PumpAdmin(admin.ModelAdmin):
    list_display = ('pump_id', 'station_id', 'pump_number', 'fuel_type', 'status', 'flow_rate')

admin.site.register(Pump, PumpAdmin)



# SystemSetting Admin

class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('setting_id', 'fuel_type', 'price_per_liter', 'updated_at')

admin.site.register(SystemSetting, SystemSettingAdmin)



# Inventory Admin

class InventoryAdmin(admin.ModelAdmin):
    list_display = ('inventory_id', 'station_id', 'fuel_type', 'quantity', 'capacity', 'min_threshold', 'unit_price', 'updated_at')

admin.site.register(Inventory, InventoryAdmin)



# Transaction Admin

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'station_id', 'user_id', 'pump_id', 'fuel_type', 'quantity', 'total_price', 'payment_method', 'car_plate', 'transaction_time')

admin.site.register(Transaction, TransactionAdmin)



# Alert Admin

class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_id', 'station', 'type', 'description', 'pump_id', 'inventory_id', 'status', 'created_at')

admin.site.register(Alert, AlertAdmin)


# Password Reset Token Admin

class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'user', 'created_at', 'expires_at', 'used')
    list_filter = ('used', 'created_at')
    readonly_fields = ('token', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'token')

admin.site.register(PasswordResetToken, PasswordResetTokenAdmin)
