# Git Commands to Push Your Work

## Step 1: Add Important Files (Excluding Cache and Database)

```bash
# Add all important source files
git add api/authentication.py
git add api/views.py
git add api/urls.py
git add service/models.py
git add service/views.py
git add service/urls.py
git add service/admin.py
git add service/backends.py
git add station/settings.py
git add templates/forgot_password.html
git add templates/reset_password.html

# Add documentation files
git add README.md
git add API_ENDPOINTS.md
git add API_URLS.txt
git add CHANGES_SUMMARY.md
git add DEPLOYMENT.md
git add FIX_MIGRATION_ERRORS.md
git add MIGRATION_GUIDE.md
git add TOKEN_AUTH_FIX.md
git add .gitignore

# Add helper scripts
git add fix_database.py
git add reset_and_fix.ps1
git add reset_and_fix.sh

# Add migrations (if you want to include them)
git add service/migrations/
```

## Step 2: Commit Your Changes

```bash
git commit -m "Fix authentication system and add token support

- Fixed plaintext password check (now uses check_password)
- Added HybridAuthentication supporting both session and token auth
- Updated all viewsets to support token authentication
- Fixed User model to extend AbstractBaseUser
- Added professional password reset with token system
- Added comprehensive API documentation
- Added deployment guides and migration helpers
- Fixed all security issues and improved code quality"
```

## Step 3: Push to Remote

```bash
# Push to current branch
git push origin base-html-restore

# Or if you want to push to main/master
git push origin main
```

## Alternative: Add All Changes (Including Migrations)

If you want to add everything except cache files:

```bash
# Add all changes
git add -A

# Remove cache files and database
git reset HEAD **/__pycache__/
git reset HEAD *.pyc
git reset HEAD db.sqlite3
git reset HEAD db.sqlite3.backup

# Commit
git commit -m "Complete project improvements and fixes"

# Push
git push origin base-html-restore
```

## Quick One-Liner (Recommended)

```bash
git add api/ service/ station/ templates/ *.md *.txt *.py .gitignore && git commit -m "Complete authentication fixes and API improvements" && git push origin base-html-restore
```


