"""
Database Fix Script
This script fixes database issues before running migrations.
Run this BEFORE running migrations if you encounter errors.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'station.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection
from service.models import SystemSetting, User

def fix_database():
    """Fix database issues"""
    print("Starting database fixes...")
    
    # Fix 1: Remove duplicate SystemSetting entries
    print("\n1. Fixing duplicate SystemSetting entries...")
    seen_fuel_types = {}
    duplicates = []
    
    for setting in SystemSetting.objects.all().order_by('-updated_at'):
        fuel_type = setting.fuel_type
        if fuel_type in seen_fuel_types:
            duplicates.append(setting.setting_id)
            print(f"   Marking duplicate: {fuel_type} (ID: {setting.setting_id})")
        else:
            seen_fuel_types[fuel_type] = setting.setting_id
    
    if duplicates:
        SystemSetting.objects.filter(setting_id__in=duplicates).delete()
        print(f"   Deleted {len(duplicates)} duplicate SystemSetting entries")
    else:
        print("   No duplicates found")
    
    # Fix 2: Set emails for users without them
    print("\n2. Fixing user emails...")
    users_fixed = 0
    for user in User.objects.filter(email__isnull=True):
        if user.username:
            user.email = f"{user.username}@fuelstation.local"
        else:
            user.email = f"user{user.user_id}@fuelstation.local"
        user.save(update_fields=['email'])
        users_fixed += 1
        print(f"   Set email for user {user.username}: {user.email}")
    
    if users_fixed == 0:
        print("   All users already have emails")
    else:
        print(f"   Fixed {users_fixed} users")
    
    print("\n✅ Database fixes completed!")
    print("\nYou can now run: python manage.py migrate")

if __name__ == '__main__':
    try:
        fix_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


