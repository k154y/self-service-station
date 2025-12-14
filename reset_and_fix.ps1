# Reset database and fix all issues for Windows PowerShell

Write-Host "⚠️  WARNING: This will DELETE your database!" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to cancel, or Enter to continue..."
Read-Host

# Backup database if it exists
if (Test-Path "db.sqlite3") {
    Write-Host "Creating backup..."
    Copy-Item "db.sqlite3" "db.sqlite3.backup"
    Write-Host "Backup created: db.sqlite3.backup" -ForegroundColor Green
}

# Delete database
Write-Host "Deleting database..."
Remove-Item -Force "db.sqlite3" -ErrorAction SilentlyContinue

# Delete migration files (keep __init__.py)
Write-Host "Cleaning old migrations..."
Get-ChildItem "service\migrations\0*.py" | Remove-Item -Force

# Create fresh migrations
Write-Host "Creating fresh migrations..." -ForegroundColor Cyan
python manage.py makemigrations

# Run migrations
Write-Host "Running migrations..." -ForegroundColor Cyan
python manage.py migrate

# Create superuser
Write-Host "Creating superuser..." -ForegroundColor Cyan
python manage.py createsuperuser

Write-Host "✅ Done! Database has been reset and fixed." -ForegroundColor Green

