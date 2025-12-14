# Fuel Station Management System

A comprehensive Django-based web application for managing fuel station operations, including pumps, inventory, transactions, alerts, and user management.

## Features

- **User Authentication & Authorization**
  - Secure password hashing
  - Role-based access control (Admin, Owner, Manager)
  - Session-based authentication
  - Password reset via email

- **Station Management**
  - Company and Station CRUD operations
  - Pump management with status tracking
  - Inventory monitoring with alerts
  - Transaction recording and reporting

- **RESTful API**
  - Django REST Framework integration
  - Custom session authentication
  - Role-based permissions
  - Comprehensive API endpoints

- **Dashboard & Analytics**
  - Real-time revenue tracking
  - Fuel dispensed statistics
  - Recent transactions
  - Alert management

## Technology Stack

- **Backend:** Django 5.2.8
- **API:** Django REST Framework 3.16.1
- **Database:** SQLite (development) / PostgreSQL (production)
- **Frontend:** Django Templates with Tailwind CSS
- **Authentication:** Custom session-based + Token authentication

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone the repository:**
```bash
git clone <repository-url>
cd self-service-station
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env` (if available)
   - Or set environment variables directly (see `DEPLOYMENT.md`)

5. **Run migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create a superuser (optional):**
```bash
python manage.py createsuperuser
```

7. **Run the development server:**
```bash
python manage.py runserver
```

8. **Access the application:**
   - Web Interface: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/
   - API: http://127.0.0.1:8000/api/v1/

## Project Structure

```
self-service-station/
├── api/                    # REST API app
│   ├── authentication.py   # Custom authentication
│   ├── serializers.py      # API serializers
│   ├── views.py           # API viewsets
│   └── urls.py            # API URL routing
├── service/                # Main application
│   ├── models.py          # Database models
│   ├── views.py           # Web views
│   ├── urls.py            # URL routing
│   └── admin.py           # Admin configuration
├── station/                # Project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI configuration
├── templates/             # HTML templates
├── static/                # Static files (CSS, JS)
└── requirements.txt       # Python dependencies
```

## User Roles

- **Admin:** Full system access, can manage all companies, stations, and users
- **Owner:** Can manage their own companies and stations, create managers
- **Manager:** Can view and manage assigned station operations

## API Endpoints

### Authentication
- `POST /api/v1/auth/token/` - Obtain authentication token (email-based)

### Resources
- `/api/v1/users/` - User management
- `/api/v1/companies/` - Company management
- `/api/v1/stations/` - Station management
- `/api/v1/pumps/` - Pump management
- `/api/v1/inventory/` - Inventory management
- `/api/v1/transactions/` - Transaction listing
- `/api/v1/alerts/` - Alert management

## Security Features

- ✅ Password hashing with Django's default hasher
- ✅ Secure password reset with token-based system
- ✅ Welcome emails for new user registrations
- ✅ Session-based authentication
- ✅ CSRF protection
- ✅ Role-based access control
- ✅ SQL injection protection (Django ORM)
- ✅ XSS protection

## Email Features

### Welcome Emails
- New users receive a welcome email when they register via signup page
- Admins/Owners receive notification when they create new users
- Email includes account details and login instructions

### Password Reset Flow
1. User requests password reset via `/forgot-password/`
2. System generates a secure token and sends email
3. User clicks link in email to `/reset-password/<token>/`
4. User sets new password
5. Token is invalidated after use

**Note:** See `EMAIL_SETUP.md` for detailed email configuration instructions.

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
```

### Applying Migrations
```bash
python manage.py migrate
```

## Production Deployment

See `DEPLOYMENT.md` for detailed production deployment instructions.

## Configuration

### Email Setup (for password reset and welcome emails)

Update `station/settings.py` or set environment variables:

```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@fuelstation.com'
```

For Gmail:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password in `EMAIL_HOST_PASSWORD`

## Troubleshooting

### Password Reset Not Working
- Check email configuration in settings
- Verify SMTP credentials
- Use console email backend for testing: `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATIC_URL` settings

### Database Errors
- Ensure migrations are up to date: `python manage.py migrate`
- Check database connection settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is for educational purposes.

## Support

For issues and questions, please open an issue on the repository.
