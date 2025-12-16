@echo off
echo Stopping Salon Management System Docker containers...
echo.

REM Stop Docker Compose services
docker-compose down

REM Stop and remove production container if it exists
docker stop salon-app 2>nul
docker rm salon-app 2>nul

echo.
echo All containers stopped.
echo.
pause

