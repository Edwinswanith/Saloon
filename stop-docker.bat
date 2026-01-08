@echo off
echo Stopping Saloon Management System Docker containers...
echo.

REM Stop Docker Compose services
docker-compose down

REM Stop and remove production container if it exists
docker stop saloon-app 2>nul
docker rm saloon-app 2>nul

echo.
echo All containers stopped.
echo.
pause

