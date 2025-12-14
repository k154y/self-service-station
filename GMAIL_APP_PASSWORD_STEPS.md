# How to Get Gmail App Password - Step by Step

## 🎯 Goal
Get a 16-character App Password from Gmail to use in your Django application.

## 📋 Step-by-Step Instructions

### Method 1: Direct Link (Easiest)

1. **Click this link:** https://myaccount.google.com/apppasswords
   - This takes you directly to the App Passwords page
   - You may need to sign in to your Google account first

2. **If the link doesn't work or you see "App passwords aren't available":**
   - You need to enable 2-Step Verification first (see Method 2 below)

---

### Method 2: Manual Navigation

#### Step 1: Go to Google Account
1. Open your web browser
2. Go to: https://myaccount.google.com/
3. Sign in with: `kwizerayves154@gmail.com`

#### Step 2: Enable 2-Step Verification (if not already enabled)
1. On the left sidebar, click **"Security"**
2. Under "How you sign in to Google", find **"2-Step Verification"**
3. Click on it
4. If it says "Off", click **"Get Started"** and follow the prompts
5. You'll need to:
   - Verify your phone number
   - Enter a verification code sent to your phone
   - Confirm the setup

#### Step 3: Generate App Password
1. After 2-Step Verification is enabled, go back to: https://myaccount.google.com/security
2. Scroll down to **"2-Step Verification"** section
3. Click on **"App passwords"** (it's a link below the 2-Step Verification toggle)
   - Direct link: https://myaccount.google.com/apppasswords

4. You'll see a page titled "App passwords"
5. At the top, you'll see a dropdown to select:
   - **App:** Select **"Mail"**
   - **Device:** Select **"Other (Custom name)"**
   - A text box appears → Type: **"Django App"** or **"Fuel Station"**

6. Click **"Generate"** button

7. **IMPORTANT:** A popup or page will show your 16-character password
   - It looks like: `abcd efgh ijkl mnop` (with spaces)
   - Or: `abcdefghijklmnop` (without spaces)
   - **COPY THIS PASSWORD IMMEDIATELY** - you can only see it once!

8. **Paste it into `station/settings.py`** at line 181:
   ```python
   EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'paste-your-16-char-password-here')
   ```

---

## 🔍 Visual Guide (What You'll See)

### On Google Account Security Page:
```
Security
├── Your devices
├── Recent security activity
├── 2-Step Verification  ← Click here first (if not enabled)
└── App passwords        ← Click here after enabling 2-Step
```

### App Passwords Page:
```
App passwords
─────────────
Select app: [Mail ▼]
Select device: [Other (Custom name) ▼]
Name: [Django App        ]
              [Generate] button
```

### After Generating:
```
Your app password is:
abcd efgh ijkl mnop

(You won't be able to see it again)
```

---

## ⚠️ Troubleshooting

### "App passwords aren't available for this account"
**Solution:** You must enable 2-Step Verification first. Go back to Security → 2-Step Verification → Get Started

### "I can't find App passwords"
**Solution:** 
- Make sure 2-Step Verification is ON
- Try direct link: https://myaccount.google.com/apppasswords
- Or: Security → 2-Step Verification → Scroll down → App passwords

### "I lost my app password"
**Solution:** 
- Go back to App passwords page
- You'll see a list of your app passwords
- Delete the old one and generate a new one

### "The link doesn't work"
**Solution:**
1. Go to https://myaccount.google.com/
2. Click "Security" (left sidebar)
3. Find "2-Step Verification" and click it
4. Scroll down on that page
5. Look for "App passwords" link

---

## ✅ Quick Checklist

- [ ] Signed in to Google Account (kwizerayves154@gmail.com)
- [ ] 2-Step Verification is enabled
- [ ] Navigated to App passwords page
- [ ] Selected "Mail" as the app
- [ ] Selected "Other (Custom name)" and typed "Django App"
- [ ] Clicked "Generate"
- [ ] Copied the 16-character password
- [ ] Pasted it into `station/settings.py` line 181
- [ ] Saved the file
- [ ] Restarted Django server

---

## 🎯 Direct Links Summary

- **Google Account Home:** https://myaccount.google.com/
- **Security Page:** https://myaccount.google.com/security
- **2-Step Verification:** https://myaccount.google.com/signinoptions/two-step-verification
- **App Passwords:** https://myaccount.google.com/apppasswords

---

## 💡 Pro Tip

After you get your app password, you can test it immediately:
1. Save it in `settings.py`
2. Restart your server
3. Try registering a new user
4. Check your email inbox!

If you see the email, it's working! ✅

