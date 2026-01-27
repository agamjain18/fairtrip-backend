@echo off
echo ========================================
echo FairShare Backend API Setup
echo ========================================
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2/3] Initializing database and seeding demo data...
echo [2.5/3] Verifying and Seeding City Data...
python seed_cities.py

echo.
echo [3/3] Starting FastAPI server with PM2...
echo.
echo ========================================
echo Server will start at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ========================================
echo.

npx -y pm2 start main.py --name fairshare-backend --interpreter python --watch --no-daemon
