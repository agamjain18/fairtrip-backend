# FairShare API - Complete Documentation

## 🚀 Server Information

**Base URL**: `http://localhost:8000`  
**API Docs**: `http://localhost:8000/docs` (Swagger UI)  
**Alternative Docs**: `http://localhost:8000/redoc`

## 🔐 Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_token_here>
```

### Demo Credentials
```
Email: john@example.com
Password: password123
```

---

## 📋 API Endpoints Reference

### 🔑 Authentication (`/auth`)

#### Register New User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "bio": "Travel enthusiast"
}
```

#### Login (Form Data)
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=john@example.com&password=password123
```

#### Login (JSON)
```http
POST /auth/login-json
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "password123"
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

---

### 👥 Users (`/users`)

#### Get All Users
```http
GET /users?skip=0&limit=100
```

#### Get User by ID
```http
GET /users/{user_id}
```

#### Update User
```http
PUT /users/{user_id}
Content-Type: application/json

{
  "full_name": "Updated Name",
  "bio": "New bio",
  "dark_mode": true,
  "push_notifications": true
}
```

#### Get User's Friends
```http
GET /users/{user_id}/friends
```

#### Get User Sessions
```http
GET /users/{user_id}/sessions
```

#### Revoke Session
```http
POST /users/{user_id}/sessions/{session_id}/revoke
```

#### Get Payment Methods
```http
GET /users/{user_id}/payment-methods
```

#### Add Payment Method
```http
POST /users/{user_id}/payment-methods
Content-Type: application/json

{
  "type": "upi",
  "name": "Google Pay",
  "identifier": "user@okaxis",
  "is_primary": true
}
```

---

### 🗺️ Trips (`/trips`)

#### Get All Trips
```http
GET /trips?user_id={user_id}&skip=0&limit=100
```

#### Get Trip by ID
```http
GET /trips/{trip_id}
```

#### Create Trip
```http
POST /trips?creator_id={user_id}
Content-Type: application/json

{
  "title": "Summer in Tokyo",
  "description": "Amazing adventure",
  "destination": "Tokyo, Japan",
  "image_url": "https://example.com/image.jpg",
  "start_date": "2024-07-15T00:00:00",
  "end_date": "2024-07-22T00:00:00",
  "total_budget": 2500.00,
  "currency": "USD",
  "is_public": false
}
```

#### Update Trip
```http
PUT /trips/{trip_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "status": "active",
  "total_budget": 3000.00
}
```

#### Add Trip Member
```http
POST /trips/{trip_id}/members/{user_id}
```

#### Remove Trip Member
```http
DELETE /trips/{trip_id}/members/{user_id}
```

#### Get Trip Members
```http
GET /trips/{trip_id}/members
```

#### Get Trip Summary
```http
GET /trips/{trip_id}/summary
```

**Response:**
```json
{
  "id": 1,
  "title": "Summer in Tokyo",
  "total_budget": 2500.00,
  "total_spent": 625.00,
  "budget_remaining": 1875.00,
  "budget_used_percentage": 25.0,
  "member_count": 5,
  "expense_count": 6,
  "itinerary_days": 3,
  "checklist_items": 6,
  "photos_count": 3
}
```

---

### 💰 Expenses (`/expenses`)

#### Get Expenses
```http
GET /expenses?trip_id={trip_id}&skip=0&limit=100
```

#### Get Expense by ID
```http
GET /expenses/{expense_id}
```

#### Create Expense
```http
POST /expenses
Content-Type: application/json

{
  "trip_id": 1,
  "title": "Dinner at Restaurant",
  "description": "Amazing sushi",
  "amount": 145.00,
  "currency": "USD",
  "category": "food_drink",
  "paid_by": 1,
  "participant_ids": [1, 2, 3, 4, 5],
  "location": "Shibuya, Tokyo",
  "split_type": "equal",
  "expense_date": "2024-07-16T19:00:00"
}
```

#### Update Expense
```http
PUT /expenses/{expense_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "amount": 150.00,
  "status": "settled"
}
```

#### Delete Expense
```http
DELETE /expenses/{expense_id}
```

#### Get Expense Participants
```http
GET /expenses/{expense_id}/participants
```

#### Add Participant
```http
POST /expenses/{expense_id}/participants/{user_id}
```

#### Create Dispute
```http
POST /expenses/{expense_id}/disputes?user_id={user_id}
Content-Type: application/json

{
  "reason": "Amount seems incorrect"
}
```

#### Get Trip Expense Summary
```http
GET /expenses/trip/{trip_id}/summary?user_id={user_id}
```

**Response:**
```json
{
  "total_spent": 625.00,
  "expense_count": 6,
  "by_category": {
    "food_drink": 190.00,
    "transport": 161.00,
    "entertainment": 60.00,
    "shopping": 12.00
  },
  "by_status": {
    "pending": 3,
    "settled": 3
  },
  "user_paid": 273.50,
  "user_share": 125.00,
  "user_balance": 148.50
}
```

---

### 📅 Itinerary (`/itinerary`)

#### Get Itinerary Days
```http
GET /itinerary/trip/{trip_id}/days
```

#### Get Day by ID
```http
GET /itinerary/days/{day_id}
```

#### Create Itinerary Day
```http
POST /itinerary/days
Content-Type: application/json

{
  "trip_id": 1,
  "day_number": 1,
  "date": "2024-07-15T00:00:00",
  "title": "Arrival Day",
  "description": "Arrive and settle in"
}
```

#### Update Day
```http
PUT /itinerary/days/{day_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "description": "New description"
}
```

#### Get Activities for Day
```http
GET /itinerary/days/{day_id}/activities
```

#### Create Activity
```http
POST /itinerary/activities
Content-Type: application/json

{
  "day_id": 1,
  "title": "Visit Temple",
  "description": "Explore ancient temple",
  "type": "sightseeing",
  "location": "Asakusa",
  "start_time": "2024-07-15T09:00:00",
  "end_time": "2024-07-15T11:00:00",
  "duration_minutes": 120,
  "cost": 0.00,
  "latitude": 35.7148,
  "longitude": 139.7967
}
```

#### Update Activity
```http
PUT /itinerary/activities/{activity_id}
```

#### Delete Activity
```http
DELETE /itinerary/activities/{activity_id}
```

---

### ✅ Checklist (`/checklist`)

#### Get Checklist Items
```http
GET /checklist/trip/{trip_id}
```

#### Create Checklist Item
```http
POST /checklist
Content-Type: application/json

{
  "trip_id": 1,
  "title": "Pack sunscreen",
  "description": "SPF 50+",
  "category": "packing",
  "priority": "high",
  "due_date": "2024-07-14T00:00:00",
  "assignee_ids": [1, 2]
}
```

#### Update Checklist Item
```http
PUT /checklist/{item_id}
Content-Type: application/json

{
  "is_completed": true,
  "priority": "medium"
}
```

#### Toggle Completion
```http
POST /checklist/{item_id}/toggle
```

#### Get Checklist Summary
```http
GET /checklist/trip/{trip_id}/summary
```

**Response:**
```json
{
  "total_items": 6,
  "completed_items": 3,
  "pending_items": 3,
  "completion_percentage": 50.0,
  "by_category": {
    "packing": {"total": 2, "completed": 0},
    "documents": {"total": 2, "completed": 2},
    "tasks": {"total": 2, "completed": 1}
  },
  "by_priority": {
    "high": {"total": 3, "completed": 2},
    "medium": {"total": 3, "completed": 1}
  }
}
```

---

### 📸 Photos, Polls & More (`/misc`)

#### Get Trip Photos
```http
GET /misc/photos/trip/{trip_id}
```

#### Upload Photo
```http
POST /misc/photos
Content-Type: application/json

{
  "trip_id": 1,
  "uploaded_by": 1,
  "url": "https://example.com/photo.jpg",
  "caption": "Amazing sunset!",
  "location": "Tokyo Tower",
  "taken_at": "2024-07-16T18:00:00"
}
```

#### Get Trip Polls
```http
GET /misc/polls/trip/{trip_id}
```

#### Create Poll
```http
POST /misc/polls
Content-Type: application/json

{
  "trip_id": 1,
  "created_by": 1,
  "question": "Where should we eat tonight?",
  "description": "Vote for dinner location",
  "ends_at": "2024-07-16T18:00:00",
  "options": [
    {"text": "Sushi Restaurant"},
    {"text": "Ramen Shop"},
    {"text": "Izakaya"}
  ]
}
```

#### Vote on Poll
```http
POST /misc/polls/{poll_id}/vote?option_id={option_id}&user_id={user_id}
```

#### Get Bucket List
```http
GET /misc/bucket-list/trip/{trip_id}
```

#### Add Bucket List Item
```http
POST /misc/bucket-list
Content-Type: application/json

{
  "trip_id": 1,
  "added_by": 1,
  "title": "Visit Mount Fuji",
  "description": "See the iconic mountain",
  "location": "Mount Fuji"
}
```

#### Complete Bucket List Item
```http
POST /misc/bucket-list/{item_id}/complete
```

#### Get Accommodations
```http
GET /misc/accommodations/trip/{trip_id}
```

#### Add Accommodation
```http
POST /misc/accommodations
Content-Type: application/json

{
  "trip_id": 1,
  "name": "Shibuya Grand Hotel",
  "type": "hotel",
  "address": "1-1-1 Shibuya, Tokyo",
  "check_in": "2024-07-15T15:00:00",
  "check_out": "2024-07-22T11:00:00",
  "booking_reference": "HTL-123456",
  "cost": 1200.00,
  "contact_number": "+81-3-1234-5678"
}
```

#### Get Flights
```http
GET /misc/flights/trip/{trip_id}
```

#### Add Flight
```http
POST /misc/flights
Content-Type: application/json

{
  "trip_id": 1,
  "airline": "Japan Airlines",
  "flight_number": "JL005",
  "departure_airport": "JFK",
  "arrival_airport": "NRT",
  "departure_time": "2024-07-15T11:00:00",
  "arrival_time": "2024-07-16T14:30:00",
  "booking_reference": "ABC123",
  "seat_number": "12A",
  "status": "scheduled"
}
```

#### Update Flight Status
```http
PUT /misc/flights/{flight_id}/status?status=boarding
```

#### Get Notifications
```http
GET /misc/notifications/user/{user_id}?unread_only=true
```

#### Mark Notification as Read
```http
POST /misc/notifications/{notification_id}/read
```

#### Mark All Notifications as Read
```http
POST /misc/notifications/user/{user_id}/read-all
```

---

## 📊 Data Models

### User
```json
{
  "id": 1,
  "email": "john@example.com",
  "username": "john_doe",
  "full_name": "John Doe",
  "avatar_url": "https://...",
  "phone": "+1234567890",
  "bio": "Travel enthusiast",
  "two_factor_enabled": true,
  "dark_mode": true,
  "total_balance": 2450.80,
  "amount_to_receive": 340.20,
  "amount_to_pay": 45.00
}
```

### Trip
```json
{
  "id": 1,
  "title": "Summer in Tokyo",
  "destination": "Tokyo, Japan",
  "start_date": "2024-07-15T00:00:00",
  "end_date": "2024-07-22T00:00:00",
  "status": "active",
  "total_budget": 2500.00,
  "total_spent": 625.00,
  "budget_used_percentage": 25.0,
  "creator_id": 1
}
```

### Expense
```json
{
  "id": 1,
  "trip_id": 1,
  "title": "Dinner at Izakaya",
  "amount": 145.00,
  "currency": "USD",
  "category": "food_drink",
  "status": "pending",
  "paid_by": 1,
  "split_type": "equal",
  "expense_date": "2024-07-16T19:00:00"
}
```

---

## 🔍 Query Parameters

### Pagination
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

### Filtering
- `trip_id`: Filter by trip ID
- `user_id`: Filter by user ID
- `unread_only`: Show only unread items (boolean)

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "detail": "User already exists"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Trip not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## 🎯 Common Use Cases

### 1. User Registration & Login Flow
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","password":"pass123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -d "username=user@example.com&password=pass123"

# Use token
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <token>"
```

### 2. Create Trip with Members
```bash
# Create trip
curl -X POST "http://localhost:8000/trips?creator_id=1" \
  -H "Content-Type: application/json" \
  -d '{"title":"Weekend Getaway","destination":"Paris"}'

# Add members
curl -X POST http://localhost:8000/trips/1/members/2
curl -X POST http://localhost:8000/trips/1/members/3
```

### 3. Add Expense and Split
```bash
curl -X POST http://localhost:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{
    "trip_id": 1,
    "title": "Dinner",
    "amount": 100.00,
    "paid_by": 1,
    "participant_ids": [1,2,3],
    "split_type": "equal"
  }'
```

---

## 🔧 Development Tips

1. **Interactive API Docs**: Visit `http://localhost:8000/docs` to test all endpoints
2. **Database Reset**: Delete `fairshare.db` and run `python seed_data.py`
3. **Hot Reload**: Server auto-reloads on code changes
4. **Logs**: Check terminal for request logs and errors

---

## 📝 Notes

- All datetime fields use ISO 8601 format
- Amounts are in decimal format (e.g., 100.00)
- Currency codes follow ISO 4217 (USD, EUR, JPY, etc.)
- Status enums are lowercase with underscores
- IDs are auto-generated integers

---

**Happy Coding! 🚀**
