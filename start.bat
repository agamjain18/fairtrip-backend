@echo off
echo ========================================
echo FairShare Backend API Setup
echo ========================================
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2/3] Initializing database and seeding demo data...
python seed_data.py

echo.
echo [3/3] Starting FastAPI server...
echo.
echo ========================================
echo Server will start at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ========================================
echo.

python main.py
