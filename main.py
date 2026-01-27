from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database_sql import init_db
from routes_sql import auth, users, trips, expenses, cities, itinerary, checklist, misc_new
from routes_sql import settlements, recurring_expenses, currency, notifications

# Initialize FastAPI app
app = FastAPI(
    title="FairShare API",
    description="Backend API for FairShare - Group Trip Management & Expense Splitting App",
    version="1.0.0",
    root_path="/fairtrip"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os
UPLOAD_DIRECTORY = "uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
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
app.include_router(cities.router)
app.include_router(itinerary.router)
app.include_router(checklist.router)
app.include_router(misc_new.router)
from routes_sql import transports, accommodations
app.include_router(transports.router)
app.include_router(accommodations.router)

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
    print("SQLite Database initialized successfully!")
    print("API Documentation available at: http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
