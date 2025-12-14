# Token Authentication Fix - Complete Guide

## Problem
The API was returning 403 errors when using token authentication because:
1. Viewsets were only using `CustomSessionAuthentication` (session-based)
2. Permission class checked `request.session.get('user_id')` which doesn't exist with token auth
3. Token authentication wasn't properly integrated

## Solution Applied

### 1. Created HybridAuthentication
- Supports both session-based and token-based authentication
- Tries token first, falls back to session
- Located in `api/authentication.py`

### 2. Updated HasCompanyAccess Permission
- Now works with both authentication methods
- Gets user info from either session or authenticated user object
- Located in `api/views.py`

### 3. Updated All ViewSets
- Changed from `CustomSessionAuthentication` to `HybridAuthentication`
- Updated `get_queryset()` methods to work with both auth types
- All viewsets now support token authentication

### 4. Enhanced Token Endpoint
- `CustomObtainAuthToken` now properly creates tokens
- Also sets session for web compatibility

## Testing in Postman

### Step 1: Get Token
**Request:**
- Method: `POST`
- URL: `http://localhost:8000/api/v1/auth/token/`
- Headers:
  - `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "email": "your-email@example.com",
    "password": "yourpassword"
}
```

**Response:**
```json
{
    "token": "c5c6cace24828d4d5704ce42eb5d63c4a9358632"
}
```

### Step 2: Use Token in API Requests
**Request:**
- Method: `GET`
- URL: `http://localhost:8000/api/v1/users/`
- Headers:
  - `Authorization: Token c5c6cace24828d4d5704ce42eb5d63c4a9358632`
  - `Content-Type: application/json`

**Expected Response:** 200 OK with user list

## Important Notes

1. **Token Format:** Must be `Token {your-token}` (with space after "Token")
2. **Header Name:** Must be exactly `Authorization` (case-sensitive)
3. **Token Validity:** Tokens don't expire unless user is deleted
4. **Session Compatibility:** Token auth also sets session, so web interface works too

## Troubleshooting

### Still Getting 403?
1. **Check token format:** Should be `Token {token}` not `Bearer {token}`
2. **Check header name:** Must be `Authorization` exactly
3. **Verify token exists:** Check database `authtoken_token` table
4. **Check user is active:** User must be authenticated and active

### Token Not Working?
1. **Regenerate token:** Delete old token and get new one
2. **Check email/password:** Make sure credentials are correct
3. **Check user exists:** Verify user exists in database

### Testing Commands

**Check if token exists in database:**
```python
python manage.py shell
from rest_framework.authtoken.models import Token
Token.objects.all()
```

**Create token manually:**
```python
from rest_framework.authtoken.models import Token
from service.models import User
user = User.objects.get(email='your-email@example.com')
token, created = Token.objects.get_or_create(user=user)
print(token.key)
```

## Files Changed

1. `api/authentication.py` - Added HybridAuthentication
2. `api/views.py` - Updated all viewsets and permission class
3. All viewsets now use HybridAuthentication instead of CustomSessionAuthentication

## Next Steps

1. Restart your Django server
2. Test token endpoint in Postman
3. Use token in Authorization header for all API requests
4. Verify all endpoints work correctly


