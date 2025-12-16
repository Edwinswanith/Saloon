@echo off
echo Starting Salon Management System with Docker...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo Docker is running...
echo.

REM Ask user which setup to use
echo Select deployment option:
echo 1. Development (Docker Compose - Frontend + Backend separate)
echo 2. Production (Single Container - Optimized build)
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo Starting development environment with Docker Compose...
    echo Frontend will be available at: http://localhost:5173
    echo Backend will be available at: http://localhost:5000
    echo.
    docker-compose up --build
) else if "%choice%"=="2" (
    echo.
    echo Building production container...
    docker build -t salon-app .
    
    echo.
    echo Starting production container...
    echo Application will be available at: http://localhost:5000
    echo.
    docker run -d --name salon-app -p 5000:5000 -v "%cd%\backend\instance:/app/instance" salon-app
    
    echo.
    echo Container started successfully!
    echo To view logs: docker logs -f salon-app
    echo To stop: docker stop salon-app
    echo To remove: docker rm salon-app
) else (
    echo Invalid choice. Please run the script again.
    pause
    exit /b 1
)

echo.
pause

