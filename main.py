from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database_sql import init_db
from routes_sql import auth, users, trips, expenses, cities, itinerary, checklist, misc_new
from routes_sql import settlements, recurring_expenses, currency, notifications, sync
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, ContentStream
import xxhash
import json

class ETagMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method != "GET":
            return await call_next(request)

        response = await call_next(request)

        # Only standard JSON responses
        if response.status_code != 200:
            return response
            
        # Capture body
        response_body = [section async for section in response.body_iterator]
        
        # Reconstruct as async iterator to satisfy Starlette
        async def async_generator():
            for item in response_body:
                yield item
        response.body_iterator = async_generator()
        
        try:
            full_body = b"".join(response_body)
            # Create ETag (xxhash is fast)
            etag = f'"{xxhash.xxh64(full_body).hexdigest()}"'
            
            # Check If-None-Match
            if request.headers.get("if-none-match") == etag:
                return Response(status_code=304)
            
            response.headers["ETag"] = etag
        except:
             pass
             
        return response

# Initialize FastAPI app
app = FastAPI(
    title="FairShare API",
    description="Backend API for FairShare - Group Trip Management & Expense Splitting App",
    version="1.0.0",
    # root_path="/fairtrip"  # Removed as it might interfere with static mount when proxy strips prefix
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["ETag"], # Important for client to see ETag
)

app.add_middleware(ETagMiddleware)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation Error for {request.url}:")
    print(f"   Body: {exc.body}")
    print(f"   Errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIRECTORY = os.path.join(BASE_DIR, "uploads")

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    
print(f"Mounting static files from: {UPLOAD_DIRECTORY}")
if os.path.exists(UPLOAD_DIRECTORY):
    print(f"   - Directory exists. Contains {len(os.listdir(UPLOAD_DIRECTORY))} files.")
else:
    print(f"   - Directory does NOT exist!")

app.mount("/static", StaticFiles(directory=UPLOAD_DIRECTORY), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(trips.router)
app.include_router(expenses.router)
app.include_router(settlements.router)
app.include_router(recurring_expenses.router)
app.include_router(currency.router)
app.include_router(notifications.router)
app.include_router(sync.router)
app.include_router(cities.router)
app.include_router(itinerary.router)
app.include_router(checklist.router)
app.include_router(misc_new.router)
from routes_sql import transports, accommodations, emergency, test_services
app.include_router(transports.router)
app.include_router(accommodations.router)
app.include_router(emergency.router)
app.include_router(test_services.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to FairShare API (SQLite Version)",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    
    # Auto-seed demo users if DB is empty
    try:
        from database_sql import SessionLocal, User
        db = SessionLocal()
        user_count = db.query(User).count()
        db.close()
        
        if user_count == 0:
            print("Database is empty. Seeding demo users...")
            from seed_sql import seed_sql_data
            seed_sql_data()
    except Exception as e:
        print(f"Failed to auto-seed demo users: {e}")

    # Auto-seed cities
    try:
        from seed_cities import seed_cities
        seed_cities()
    except Exception as e:
        print(f"Failed to auto-seed cities: {e}")

    print("SQLite Database initialized successfully!")
    port = os.getenv("PORT", "8005")
    print(f"API Documentation available at: http://localhost:{port}/docs")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8005))
    # Reload is handled by PM2 watch feature in production
    is_prod = os.getenv("ENV", "production") == "production"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=not is_prod)
