@echo off
set PROJECT_ID=legel-assistent-466812
set REPOSITORY_NAME=saloon
set REGION=europe-west2
set IMAGE_NAME=saloon-management-system
set IMAGE_TAG=v59
set SERVICE_NAME=saloon-management-system

REM Authenticate with Google Cloud
echo Authenticating with Google Cloud...
call gcloud auth configure-docker %REGION%-docker.pkg.dev --quiet
if errorlevel 1 goto :fail

REM Set the project
call gcloud config set project %PROJECT_ID%
if errorlevel 1 goto :fail

REM gcloud artifacts repositories create %REPOSITORY_NAME% --repository-format=docker --location=%REGION%

docker build --no-cache --build-arg VITE_PUBLIC_BASE_URL=https://saloon-management-system-895210689446.europe-west2.run.app -t %IMAGE_NAME%:%IMAGE_TAG% .
if errorlevel 1 goto :fail

docker tag %IMAGE_NAME%:%IMAGE_TAG% %REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%IMAGE_NAME%:%IMAGE_TAG%
if errorlevel 1 goto :fail

docker push %REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%IMAGE_NAME%:%IMAGE_TAG%
if errorlevel 1 goto :fail

call gcloud run deploy %SERVICE_NAME% --image %REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%IMAGE_NAME%:%IMAGE_TAG% --platform managed --region %REGION% --allow-unauthenticated --timeout=600s --min-instances=1 --memory=512Mi --concurrency=80 --cpu=1 --set-env-vars "MONGODB_URI=mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon&tls=true&retryWrites=true&w=majority"
if errorlevel 1 goto :fail

echo.
echo [OK] Deploy finished. Image tag: %IMAGE_TAG%
goto :eof

:fail
echo.
echo [ERROR] Deploy failed at a previous step. See output above.
exit /b 1
