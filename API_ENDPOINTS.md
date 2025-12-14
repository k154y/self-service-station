# Complete API Endpoints List

Base URL: `http://localhost:8000/api/v1/`

## Authentication Endpoints

### 1. Token Authentication (Email-based Login)
```
POST http://localhost:8000/api/v1/auth/token/
```
**Request Body (JSON):**
```json
{
    "email": "user@example.com",
    "password": "yourpassword"
}
```
**Response:**
```json
{
    "token": "your-auth-token-here"
}
```

---

## User Endpoints

### List Users
```
GET http://localhost:8000/api/v1/users/
```

### Get User by ID
```
GET http://localhost:8000/api/v1/users/{user_id}/
```
Example: `http://localhost:8000/api/v1/users/1/`

### Create User
```
POST http://localhost:8000/api/v1/users/
```
**Request Body (JSON):**
```json
{
    "username": "newuser",
    "full_name": "New User",
    "email": "newuser@example.com",
    "password": "password123",
    "role": "manager"
}
```

### Update User (Full)
```
PUT http://localhost:8000/api/v1/users/{user_id}/
```
Example: `http://localhost:8000/api/v1/users/1/`

### Update User (Partial)
```
PATCH http://localhost:8000/api/v1/users/{user_id}/
```
Example: `http://localhost:8000/api/v1/users/1/`

### Delete User
```
DELETE http://localhost:8000/api/v1/users/{user_id}/
```
Example: `http://localhost:8000/api/v1/users/1/`

---

## Company Endpoints

### List Companies
```
GET http://localhost:8000/api/v1/companies/
```

### Get Company by ID
```
GET http://localhost:8000/api/v1/companies/{company_id}/
```
Example: `http://localhost:8000/api/v1/companies/1/`

### Create Company
```
POST http://localhost:8000/api/v1/companies/
```
**Request Body (JSON):**
```json
{
    "name": "Company Name",
    "owner": 1
}
```

### Update Company (Full)
```
PUT http://localhost:8000/api/v1/companies/{company_id}/
```
Example: `http://localhost:8000/api/v1/companies/1/`

### Update Company (Partial)
```
PATCH http://localhost:8000/api/v1/companies/{company_id}/
```
Example: `http://localhost:8000/api/v1/companies/1/`

### Delete Company
```
DELETE http://localhost:8000/api/v1/companies/{company_id}/
```
Example: `http://localhost:8000/api/v1/companies/1/`

---

## Station Endpoints

### List Stations
```
GET http://localhost:8000/api/v1/stations/
```

### Get Station by ID
```
GET http://localhost:8000/api/v1/stations/{station_id}/
```
Example: `http://localhost:8000/api/v1/stations/1/`

### Create Station
```
POST http://localhost:8000/api/v1/stations/
```
**Request Body (JSON):**
```json
{
    "company_id": 1,
    "manager_id": 2,
    "name": "Station Name",
    "location": "Station Location",
    "status": "active"
}
```

### Update Station (Full)
```
PUT http://localhost:8000/api/v1/stations/{station_id}/
```
Example: `http://localhost:8000/api/v1/stations/1/`

### Update Station (Partial)
```
PATCH http://localhost:8000/api/v1/stations/{station_id}/
```
Example: `http://localhost:8000/api/v1/stations/1/`

### Delete Station
```
DELETE http://localhost:8000/api/v1/stations/{station_id}/
```
Example: `http://localhost:8000/api/v1/stations/1/`

---

## Pump Endpoints

### List Pumps
```
GET http://localhost:8000/api/v1/pumps/
```

### Get Pump by ID
```
GET http://localhost:8000/api/v1/pumps/{pump_id}/
```
Example: `http://localhost:8000/api/v1/pumps/1/`

### Create Pump
```
POST http://localhost:8000/api/v1/pumps/
```
**Request Body (JSON):**
```json
{
    "station": 1,
    "pump_number": 1,
    "fuel_type": "Petrol",
    "status": "active",
    "flow_rate": 50.0
}
```

### Update Pump (Full)
```
PUT http://localhost:8000/api/v1/pumps/{pump_id}/
```
Example: `http://localhost:8000/api/v1/pumps/1/`

### Update Pump (Partial)
```
PATCH http://localhost:8000/api/v1/pumps/{pump_id}/
```
Example: `http://localhost:8000/api/v1/pumps/1/`

### Delete Pump
```
DELETE http://localhost:8000/api/v1/pumps/{pump_id}/
```
Example: `http://localhost:8000/api/v1/pumps/1/`

### Update Pump Status (Custom Action)
```
PATCH http://localhost:8000/api/v1/pumps/{pump_id}/status-update/
```
Example: `http://localhost:8000/api/v1/pumps/1/status-update/`
**Request Body (JSON):**
```json
{
    "status": "active"
}
```
**Note:** Status must be one of: `"active"` or `"offline"`

---

## Inventory Endpoints

### List Inventory
```
GET http://localhost:8000/api/v1/inventory/
```

### Get Inventory by ID
```
GET http://localhost:8000/api/v1/inventory/{inventory_id}/
```
Example: `http://localhost:8000/api/v1/inventory/1/`

### Update Inventory (Partial Only - Managers cannot update)
```
PATCH http://localhost:8000/api/v1/inventory/{inventory_id}/
```
Example: `http://localhost:8000/api/v1/inventory/1/`
**Request Body (JSON):**
```json
{
    "quantity": 1000.0,
    "unit_price": 1500.00,
    "min_threshold": 100.0
}
```
**Note:** 
- Creation via API is forbidden
- Deletion via API is forbidden
- Only `quantity`, `unit_price`, and `min_threshold` can be updated

---

## Transaction Endpoints

### List Transactions (with filtering)
```
GET http://localhost:8000/api/v1/transactions/
```

### Get Transaction by ID
```
GET http://localhost:8000/api/v1/transactions/{transaction_id}/
```
Example: `http://localhost:8000/api/v1/transactions/1/`

### Create Transaction
```
POST http://localhost:8000/api/v1/transactions/create/
```
**Request Body (JSON):**
```json
{
    "station_id": 1,
    "user_id": 1,
    "pump_id": 1,
    "fuel_type": "Petrol",
    "quantity": 20.5,
    "payment_method": "cash",
    "car_plate": "ABC123"
}
```
**Note:** `total_price` is calculated automatically server-side

### Filter Transactions (Query Parameters)
```
GET http://localhost:8000/api/v1/transactions/?search=ABC123
GET http://localhost:8000/api/v1/transactions/?duration=24hrs
GET http://localhost:8000/api/v1/transactions/?duration=week
GET http://localhost:8000/api/v1/transactions/?duration=month
GET http://localhost:8000/api/v1/transactions/?payment_method=cash
GET http://localhost:8000/api/v1/transactions/?station_id=1
GET http://localhost:8000/api/v1/transactions/?search=Petrol&duration=24hrs&payment_method=cash
```

**Query Parameters:**
- `search` - Search by fuel_type, payment_method, car_plate, or transaction_id
- `duration` - Filter by time: `24hrs`, `week`, `month`, or `all` (default)
- `payment_method` - Filter by payment method: `cash`, `momo`, `card`, or `all` (default)
- `station_id` - Filter by station ID (Admin/Owner only)

---

## Alert Endpoints

### List Alerts (with filtering)
```
GET http://localhost:8000/api/v1/alerts/
```

### Get Alert by ID
```
GET http://localhost:8000/api/v1/alerts/{alert_id}/
```
Example: `http://localhost:8000/api/v1/alerts/1/`

### Update Alert Status (Partial - Only status field)
```
PATCH http://localhost:8000/api/v1/alerts/{alert_id}/
```
Example: `http://localhost:8000/api/v1/alerts/1/`
**Request Body (JSON):**
```json
{
    "status": "resolved"
}
```
**Note:** 
- Only the `status` field can be updated
- Status must be one of: `"pending"`, `"resolved"`, or `"ignored"`
- Creation and deletion via API are not allowed

### Filter Alerts (Query Parameters)
```
GET http://localhost:8000/api/v1/alerts/?status=pending
GET http://localhost:8000/api/v1/alerts/?status=resolved
GET http://localhost:8000/api/v1/alerts/?type=inventory
GET http://localhost:8000/api/v1/alerts/?company_id=1
GET http://localhost:8000/api/v1/alerts/?station_id=1
```

**Query Parameters:**
- `status` - Filter by status: `pending`, `resolved`, `ignored`, or `all` (default: `pending`)
- `type` - Filter by type: `security`, `maintenance`, `inventory`, `system`, or `all`
- `company_id` - Filter by company (Admin only)
- `station_id` - Filter by station (Admin/Owner only)

---

## Authentication Methods

### Method 1: Session Authentication (Web Browser)
- Login via web interface: `http://localhost:8000/`
- Session cookie is automatically used for API requests

### Method 2: Token Authentication (API/Mobile)
1. Get token: `POST http://localhost:8000/api/v1/auth/token/`
2. Include in headers: `Authorization: Token {your-token-here}`

### Method 3: Basic Authentication
- Include in headers: `Authorization: Basic {base64-encoded-credentials}`

---

## Postman Collection Setup

### Headers for Token Authentication:
```
Authorization: Token your-token-here
Content-Type: application/json
```

### Headers for Session Authentication:
```
Cookie: sessionid=your-session-id
Content-Type: application/json
X-CSRFToken: your-csrf-token
```

### Example Postman Request:
1. **Method:** POST
2. **URL:** `http://localhost:8000/api/v1/auth/token/`
3. **Headers:**
   - `Content-Type: application/json`
4. **Body (raw JSON):**
   ```json
   {
       "email": "admin@fuelstation.rw",
       "password": "yourpassword"
   }
   ```
5. **Response:** Copy the token from response
6. **For subsequent requests:** Add header `Authorization: Token {token-from-step-5}`

---

## Quick Copy-Paste URLs

### Authentication
```
http://localhost:8000/api/v1/auth/token/
```

### Users
```
http://localhost:8000/api/v1/users/
http://localhost:8000/api/v1/users/1/
```

### Companies
```
http://localhost:8000/api/v1/companies/
http://localhost:8000/api/v1/companies/1/
```

### Stations
```
http://localhost:8000/api/v1/stations/
http://localhost:8000/api/v1/stations/1/
```

### Pumps
```
http://localhost:8000/api/v1/pumps/
http://localhost:8000/api/v1/pumps/1/
http://localhost:8000/api/v1/pumps/1/status-update/
```

### Inventory
```
http://localhost:8000/api/v1/inventory/
http://localhost:8000/api/v1/inventory/1/
```

### Transactions
```
http://localhost:8000/api/v1/transactions/
http://localhost:8000/api/v1/transactions/1/
http://localhost:8000/api/v1/transactions/create/
```

### Alerts
```
http://localhost:8000/api/v1/alerts/
http://localhost:8000/api/v1/alerts/1/
```

---

## Notes

- All endpoints require authentication (except token endpoint)
- Replace `{id}` placeholders with actual IDs (e.g., `1`, `2`, etc.)
- All POST/PUT/PATCH requests require `Content-Type: application/json` header
- Query parameters can be combined (e.g., `?status=pending&type=inventory`)
- Role-based access control applies - Admin sees all, Owner sees their companies, Manager sees assigned stations


