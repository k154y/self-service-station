#!/bin/bash
# Reset database and fix all issues
# For Windows PowerShell, use reset_and_fix.ps1 instead

echo "⚠️  WARNING: This will DELETE your database!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Backup database if it exists
if [ -f "db.sqlite3" ]; then
    echo "Creating backup..."
    cp db.sqlite3 db.sqlite3.backup
    echo "Backup created: db.sqlite3.backup"
fi

# Delete database
echo "Deleting database..."
rm -f db.sqlite3

# Delete migration files (keep __init__.py)
echo "Cleaning old migrations..."
find service/migrations -name "0*.py" -delete

# Create fresh migrations
echo "Creating fresh migrations..."
python manage.py makemigrations

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser
echo "Creating superuser..."
python manage.py createsuperuser

echo "✅ Done! Database has been reset and fixed."


