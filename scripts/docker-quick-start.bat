@echo off
REM Quick Start Script for Docker Compose - Dwaraka Mess System

echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║          DWARAKA MESS SYSTEM - DOCKER QUICK START                         ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

echo [Step 1/6] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not running
    echo.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/
    echo Then run this script again.
    pause
    exit /b 1
)
echo ✓ Docker is installed

echo.
echo [Step 2/6] Checking environment file...
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo ✓ .env file created
) else (
    echo ✓ .env file exists
)

echo.
echo [Step 3/6] Stopping any existing containers...
docker-compose down >nul 2>&1
echo ✓ Cleanup complete

echo.
echo [Step 4/6] Building and starting services...
echo This may take 3-5 minutes on first run (downloading images)...
docker-compose up -d --build
if errorlevel 1 (
    echo ❌ Failed to start services
    pause
    exit /b 1
)
echo ✓ Services started

echo.
echo [Step 5/6] Waiting for PostgreSQL to be ready...
timeout /t 15 /nobreak >nul
echo ✓ PostgreSQL should be ready

echo.
echo [Step 6/6] Initializing database...
docker exec -it dwaraka_mess_app python init_db.py
if errorlevel 1 (
    echo ⚠️  Database initialization may have failed
    echo You can try again with: docker exec -it dwaraka_mess_app python init_db.py
) else (
    echo ✓ Database initialized with sample data
)

echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║                        ✅ SETUP COMPLETE!                                 ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.
echo 🌐 Open your browser: http://localhost:5000
echo.
echo 📋 LOGIN CREDENTIALS:
echo    Admin:   Phone: 9999999999   ^| Password: admin123
echo    Student: Phone: 8111111111   ^| Password: student123
echo.
echo 📊 USEFUL COMMANDS:
echo    View logs:        docker-compose logs -f
echo    Stop services:    docker-compose down
echo    Restart:          docker-compose restart
echo    Check status:     docker-compose ps
echo.
pause
