# Email Configuration Guide

This guide will help you configure email sending for the Fuel Station Management System.

## Quick Setup for Gmail

1. **Enable App Passwords in Gmail:**
   - Go to your Google Account settings
   - Navigate to Security → 2-Step Verification
   - Scroll down to "App passwords"
   - Generate a new app password for "Mail"
   - Copy the 16-character password

2. **Set Environment Variables:**
   
   Create a `.env` file in your project root (or set environment variables):

   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-character-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

3. **Alternative: Update settings.py directly:**
   
   Edit `station/settings.py` and update these lines:
   
   ```python
   EMAIL_HOST_USER = 'your-email@gmail.com'
   EMAIL_HOST_PASSWORD = 'your-16-character-app-password'
   DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
   ```

## Testing Email Configuration

1. **For Development (Console Output):**
   - Set `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`
   - Emails will be printed to the console/terminal

2. **For Production (Real Emails):**
   - Set `EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'`
   - Configure SMTP settings as shown above

## Other Email Providers

### Outlook/Hotmail:
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### Yahoo:
```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### Custom SMTP Server:
```env
EMAIL_HOST=your-smtp-server.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-username
EMAIL_HOST_PASSWORD=your-password
```

## Troubleshooting

- **"Authentication failed"**: Make sure you're using an App Password for Gmail, not your regular password
- **"Connection refused"**: Check your firewall and ensure port 587 is open
- **"Email not received"**: Check spam folder, verify recipient email is correct
- **"SMTP server error"**: Verify EMAIL_HOST and EMAIL_PORT are correct for your provider

## Security Note

Never commit your email credentials to version control. Always use environment variables or a `.env` file that is in `.gitignore`.

