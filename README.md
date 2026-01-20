# FairShare Backend API

Complete FastAPI backend for the FairShare trip management and expense splitting application.

## 🚀 Features

- **Authentication**: JWT-based authentication with registration and login
- **User Management**: User profiles, friends, sessions, payment methods
- **Trip Management**: Create and manage trips with members
- **Expense Tracking**: Split expenses, track payments, handle disputes
- **Itinerary Planning**: Day-by-day itinerary with activities
- **Checklist**: Task management with assignees and categories
- **Photos**: Trip photo gallery
- **Polls**: Group decision making
- **Bucket List**: Track must-do activities
- **Accommodations & Flights**: Travel booking management
- **Notifications**: Real-time user notifications

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── database.py            # SQLAlchemy models and database setup
├── schemas.py             # Pydantic schemas for validation
├── seed_data.py           # Demo data seeder
├── requirements.txt       # Python dependencies
├── routes/
│   ├── __init__.py
│   ├── auth.py           # Authentication routes
│   ├── users.py          # User management routes
│   ├── trips.py          # Trip management routes
│   ├── expenses.py       # Expense tracking routes
│   ├── itinerary.py      # Itinerary routes
│   ├── checklist.py      # Checklist routes
│   └── misc.py           # Photos, polls, flights, etc.
└── fairshare.db          # SQLite database (created on first run)
```

## 🛠️ Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Initialize database and seed demo data:**
```bash
python seed_data.py
```

3. **Run the server:**
```bash
python main.py
```

Or use uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Authentication

### Register a new user:
```bash
POST /auth/register
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "John Doe"
}
```

### Login:
```bash
POST /auth/login
Form Data:
  username: user@example.com
  password: password123

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Use the token:
Add to headers: `Authorization: Bearer <access_token>`

## 📊 Demo Data

The seed script creates:
- 5 demo users (john@example.com, sarah@example.com, etc.)
- 3 trips (Tokyo, Paris, Bali)
- Multiple expenses, itinerary days, activities
- Checklist items, photos, polls
- Accommodations, flights, notifications

**Demo Login:**
- Email: `john@example.com`
- Password: `password123`

## 🔗 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with credentials
- `GET /auth/me` - Get current user info

### Users
- `GET /users` - Get all users
- `GET /users/{user_id}` - Get user by ID
- `PUT /users/{user_id}` - Update user
- `GET /users/{user_id}/friends` - Get user's friends
- `GET /users/{user_id}/payment-methods` - Get payment methods

### Trips
- `GET /trips` - Get all trips
- `POST /trips` - Create new trip
- `GET /trips/{trip_id}` - Get trip details
- `PUT /trips/{trip_id}` - Update trip
- `POST /trips/{trip_id}/members/{user_id}` - Add member
- `GET /trips/{trip_id}/summary` - Get trip summary

### Expenses
- `GET /expenses?trip_id={trip_id}` - Get trip expenses
- `POST /expenses` - Create expense
- `PUT /expenses/{expense_id}` - Update expense
- `DELETE /expenses/{expense_id}` - Delete expense
- `GET /expenses/trip/{trip_id}/summary` - Get expense summary

### Itinerary
- `GET /itinerary/trip/{trip_id}/days` - Get itinerary days
- `POST /itinerary/days` - Create itinerary day
- `GET /itinerary/days/{day_id}/activities` - Get activities
- `POST /itinerary/activities` - Create activity

### Checklist
- `GET /checklist/trip/{trip_id}` - Get checklist items
- `POST /checklist` - Create checklist item
- `POST /checklist/{item_id}/toggle` - Toggle completion
- `GET /checklist/trip/{trip_id}/summary` - Get summary

### Miscellaneous
- `GET /misc/photos/trip/{trip_id}` - Get trip photos
- `GET /misc/polls/trip/{trip_id}` - Get trip polls
- `POST /misc/polls/{poll_id}/vote` - Vote on poll
- `GET /misc/bucket-list/trip/{trip_id}` - Get bucket list
- `GET /misc/accommodations/trip/{trip_id}` - Get accommodations
- `GET /misc/flights/trip/{trip_id}` - Get flights
- `GET /misc/notifications/user/{user_id}` - Get notifications

## 🗄️ Database Models

- **User**: User accounts with settings and wallet info
- **Trip**: Trip details with budget tracking
- **Expense**: Expense records with split calculations
- **ItineraryDay**: Daily itinerary structure
- **Activity**: Individual activities in itinerary
- **ChecklistItem**: Tasks with assignees
- **Photo**: Trip photos
- **Poll**: Group polls with options and votes
- **BucketListItem**: Must-do activities
- **Accommodation**: Hotel/stay bookings
- **Flight**: Flight information
- **Notification**: User notifications
- **PaymentMethod**: User payment methods
- **Transaction**: Financial transactions

## 🔧 Configuration

Edit `database.py` to change database settings:
```python
DATABASE_URL = "sqlite:///./fairshare.db"
```

For production, use PostgreSQL:
```python
DATABASE_URL = "postgresql://user:password@localhost/fairshare"
```

## 📝 Notes

- Default password for all demo users: `password123`
- JWT secret key should be changed in production (routes/auth.py)
- CORS is set to allow all origins - restrict in production
- SQLite is used by default - consider PostgreSQL for production

## 🚀 Deployment

For production deployment:

1. Set environment variables:
```bash
export DATABASE_URL="postgresql://..."
export SECRET_KEY="your-secret-key"
```

2. Use a production ASGI server:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📄 License

MIT License - Feel free to use for your projects!
