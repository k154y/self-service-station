# Fix Migration Errors - Complete Guide

## Problem Summary

You encountered two errors:
1. **UNIQUE constraint failed on SystemSetting.fuel_type** - Duplicate entries in database
2. **Email field default issue** - Wrong default value type

## Solution Options

### Option 1: Quick Fix (Recommended - Deletes Data)

Since you said we can delete data, the easiest solution is to reset the database:

**For Windows PowerShell:**
```powershell
.\reset_and_fix.ps1
```

**For Linux/Mac:**
```bash
chmod +x reset_and_fix.sh
./reset_and_fix.sh
```

**Or manually:**
```powershell
# 1. Backup (optional)
Copy-Item db.sqlite3 db.sqlite3.backup

# 2. Delete database
Remove-Item db.sqlite3

# 3. Delete old migrations (keep __init__.py)
Get-ChildItem service\migrations\0*.py | Remove-Item

# 4. Create fresh migrations
python manage.py makemigrations

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser
```

### Option 2: Fix Existing Database (Preserves Data)

If you want to keep your data:

1. **Activate virtual environment:**
   ```powershell
   .\env\Scripts\Activate.ps1
   ```

2. **Run the fix script:**
   ```powershell
   python fix_database.py
   ```

3. **Mark problematic migrations as applied (if needed):**
   ```powershell
   python manage.py migrate service 0003 --fake
   python manage.py migrate service 0004 --fake
   ```

4. **Run remaining migrations:**
   ```powershell
   python manage.py migrate
   ```

### Option 3: Manual Database Fix

If the scripts don't work, fix manually:

1. **Open Django shell:**
   ```powershell
   python manage.py shell
   ```

2. **Remove duplicate SystemSettings:**
   ```python
   from service.models import SystemSetting
   
   # Find duplicates
   from collections import Counter
   fuel_types = SystemSetting.objects.values_list('fuel_type', flat=True)
   duplicates = [ft for ft, count in Counter(fuel_types).items() if count > 1]
   
   # Keep only the most recent for each fuel_type
   for fuel_type in duplicates:
       settings = SystemSetting.objects.filter(fuel_type=fuel_type).order_by('-updated_at')
       # Delete all except the first (most recent)
       for setting in settings[1:]:
           setting.delete()
   ```

3. **Fix user emails:**
   ```python
   from service.models import User
   
   for user in User.objects.filter(email__isnull=True):
       if user.username:
           user.email = f"{user.username}@fuelstation.local"
       else:
           user.email = f"user{user.user_id}@fuelstation.local"
       user.save()
   ```

4. **Exit shell and run migrations:**
   ```python
   exit()
   ```
   ```powershell
   python manage.py migrate
   ```

## What Was Fixed

### Migration 0004
- Added function to remove duplicate SystemSetting entries before adding unique constraint
- This prevents the UNIQUE constraint error

### Migration 0007
- Fixed email default (was using `timezone.now` which is wrong)
- Added data migration to set emails for users without them
- Now uses proper string email addresses

## After Fixing

1. **Test the application:**
   ```powershell
   python manage.py runserver
   ```

2. **Verify login works:**
   - Try logging in with existing users
   - Check that emails are set correctly

3. **Test password reset:**
   - Request password reset
   - Verify email functionality

## Troubleshooting

### If migrations still fail:
1. Check which migration is failing
2. Use `--fake` to mark it as applied (if data is already correct)
3. Or delete that specific migration and recreate it

### If you get "table already exists" errors:
- The migration was partially applied
- Use `--fake` to mark it as applied
- Or reset the database completely

### If you get "no such table" errors:
- Run `python manage.py migrate` from scratch
- Or reset the database

## Notes

- **Option 1 (Reset)** is fastest and cleanest if you can delete data
- **Option 2 (Fix)** preserves data but requires more steps
- The migrations have been updated to handle these issues automatically in the future

