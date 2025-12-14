# Migration Guide for User Model Changes

## Important: User Model Migration

The User model has been updated to extend `AbstractBaseUser` to fix the `REQUIRED_FIELDS` error. This requires database changes.

## Steps to Migrate

### Option 1: Fresh Start (Recommended if you can delete data)

1. **Backup your database** (if you have important data):
   ```bash
   # For SQLite
   cp db.sqlite3 db.sqlite3.backup
   ```

2. **Delete existing migrations** (optional, for clean start):
   ```bash
   # Delete migration files (keep __init__.py)
   rm service/migrations/0*.py
   ```

3. **Delete the database** (if using SQLite):
   ```bash
   rm db.sqlite3
   ```

4. **Create fresh migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

### Option 2: Preserve Existing Data

If you have existing users and want to preserve them:

1. **Create the migration**:
   ```bash
   python manage.py makemigrations service
   ```

2. **Before running migrate, you may need to manually update existing users**:
   - Ensure all users have email addresses
   - The password field will be automatically handled by Django

3. **Run the migration**:
   ```bash
   python manage.py migrate
   ```

4. **If migration fails due to missing emails**, run this in Django shell:
   ```python
   python manage.py shell
   ```
   ```python
   from service.models import User
   # Update users without email
   for user in User.objects.filter(email__isnull=True):
       user.email = f"{user.username}@example.com"  # Set a default email
       user.save()
   ```

## Changes Made to User Model

1. **Now extends `AbstractBaseUser`** instead of `models.Model`
2. **Email is now required** (was nullable before)
3. **Password field** is now handled by AbstractBaseUser (no length limit)
4. **Added `USERNAME_FIELD = 'email'`** - email is used for authentication
5. **Added `REQUIRED_FIELDS = ['username', 'full_name']`**
6. **Added UserManager** for creating users
7. **Added authentication methods** (is_staff, is_superuser, has_perm, etc.)

## Testing After Migration

1. **Test login**:
   - Try logging in with existing users
   - Verify password hashing works

2. **Test password reset**:
   - Request password reset
   - Verify email is sent
   - Test reset link

3. **Test API**:
   - Verify API authentication works
   - Test token generation

## Troubleshooting

### Error: "email field cannot be null"
- Solution: Update existing users to have emails (see Option 2 above)

### Error: "password field too short"
- Solution: AbstractBaseUser handles passwords automatically, this shouldn't occur

### Error: "User matching query does not exist"
- Solution: Recreate users or check email addresses

## Notes

- **AbstractBaseUser** provides `password` and `last_login` fields automatically
- **Password hashing** is handled automatically by Django
- **Email is now the primary identifier** for authentication
- **Username is still required** but not used for login


