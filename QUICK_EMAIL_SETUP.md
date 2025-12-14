# Quick Email Setup Guide

## ⚠️ Current Issue
You're seeing: "User created successfully, but we could not send a welcome email"

This means your email credentials are not configured. Follow these steps:

## 🚀 Quick Setup (5 minutes)

### Step 1: Get Gmail App Password

1. Go to https://myaccount.google.com/
2. Click **Security** (left sidebar)
3. Under "How you sign in to Google", click **2-Step Verification**
   - If not enabled, enable it first
4. Scroll down and click **App passwords**
5. Select:
   - App: **Mail**
   - Device: **Other (Custom name)** → Type "Django App"
6. Click **Generate**
7. **Copy the 16-character password** (it looks like: `abcd efgh ijkl mnop`)

### Step 2: Configure settings.py

Open `station/settings.py` and find these lines (around line 160-161):

```python
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'kwizerayves154@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')  # <-- PUT YOUR APP PASSWORD HERE
```

**Replace the empty string with your 16-character app password:**

```python
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'kwizerayves154@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'abcd efgh ijkl mnop')  # Your app password (remove spaces or keep them)
```

**Important:** 
- Use the 16-character app password, NOT your regular Gmail password
- You can include or remove spaces - both work

### Step 3: Restart Your Server

After saving `settings.py`, restart your Django server:

```bash
# Stop the server (Ctrl+C)
# Then restart:
python manage.py runserver
```

### Step 4: Test It!

1. Try registering a new user
2. Or request a password reset
3. Check your email inbox (and spam folder)

## ✅ Success Indicators

- ✅ No error message about email sending
- ✅ Success message: "Account created successfully! Please check your email for welcome message."
- ✅ Email appears in your inbox

## 🔧 Alternative: Use Environment Variables

If you prefer not to hardcode credentials in settings.py:

1. Create a `.env` file in your project root:
```env
EMAIL_HOST_USER=kwizerayves154@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
```

2. Install python-decouple (optional but recommended):
```bash
pip install python-decouple
```

3. Update settings.py to use decouple (or keep using os.environ.get)

## 🐛 Troubleshooting

**"Authentication failed"**
- ✅ Make sure you're using App Password, not regular password
- ✅ Check that 2-Step Verification is enabled
- ✅ Verify the app password is correct (no typos)

**"Connection refused"**
- ✅ Check your internet connection
- ✅ Verify firewall isn't blocking port 587
- ✅ Try using port 465 with EMAIL_USE_SSL = True instead of EMAIL_USE_TLS

**"Email not received"**
- ✅ Check spam/junk folder
- ✅ Verify recipient email is correct
- ✅ Wait a few minutes (Gmail can be slow sometimes)

**Still not working?**
- Try console backend first to see if emails are being generated:
  ```python
  EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
  ```
  This will print emails to your terminal/console instead of sending them.

## 📧 Other Email Providers

### Outlook/Hotmail
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@outlook.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

### Yahoo
```python
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@yahoo.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## 🔒 Security Note

- Never commit your email password to Git
- Use environment variables for production
- Consider using a dedicated email account for your application

