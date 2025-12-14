# Deployment Guide

This guide will help you deploy the Fuel Station Management System to production.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL (recommended for production) or SQLite (for development)
- Web server (Nginx, Apache, or similar)
- WSGI server (Gunicorn, uWSGI, or similar)

## Environment Setup

1. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
Create a `.env` file in the project root (or set environment variables):
```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@fuelstation.com
```

## Database Setup

1. **Run migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

2. **Create a superuser (if needed):**
```bash
python manage.py createsuperuser
```

## Static Files

1. **Collect static files:**
```bash
python manage.py collectstatic --noinput
```

## Security Checklist

Before deploying to production, ensure:

- [ ] `DEBUG = False` in settings.py
- [ ] `SECRET_KEY` is set via environment variable
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] HTTPS is enabled (SSL certificate configured)
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] Database credentials are secure
- [ ] Email credentials are secure
- [ ] Static files are served correctly

## Running the Server

### Development
```bash
python manage.py runserver
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn station.wsgi:application --bind 0.0.0.0:8000
```

### Production (with Nginx + Gunicorn)

1. **Create a systemd service file** (`/etc/systemd/system/fuelstation.service`):
```ini
[Unit]
Description=Gunicorn instance for Fuel Station
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/self-service-station
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn --workers 3 --bind unix:/path/to/self-service-station/fuelstation.sock station.wsgi:application

[Install]
WantedBy=multi-user.target
```

2. **Nginx configuration** (`/etc/nginx/sites-available/fuelstation`):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/self-service-station/staticfiles/;
    }

    location /media/ {
        alias /path/to/self-service-station/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/self-service-station/fuelstation.sock;
    }
}
```

## Email Configuration

For password reset functionality to work, configure email settings:

1. **Gmail Setup:**
   - Enable 2-factor authentication
   - Generate an App Password
   - Use the App Password in `EMAIL_HOST_PASSWORD`

2. **Other SMTP Servers:**
   - Update `EMAIL_HOST`, `EMAIL_PORT`, and `EMAIL_USE_TLS` accordingly

## Monitoring and Maintenance

- Set up logging
- Configure backups for the database
- Monitor disk space for static files and media
- Set up error tracking (Sentry, etc.)
- Regular security updates

## Troubleshooting

### Password Reset Not Working
- Check email configuration in settings
- Verify SMTP credentials
- Check email backend (use console backend for testing)

### Static Files Not Loading
- Run `collectstatic` command
- Check `STATIC_ROOT` and `STATIC_URL` settings
- Verify web server configuration

### Database Errors
- Check database connection settings
- Ensure migrations are up to date
- Verify database user permissions


