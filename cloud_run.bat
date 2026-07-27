@echo off
set PROJECT_ID=legel-assistent-466812
set REPOSITORY_NAME=saloon
set REGION=europe-west2
set IMAGE_NAME=saloon-management-system
set IMAGE_TAG=v70
set SERVICE_NAME=saloon-management-system

if not exist .env (
  echo [ERROR] Missing .env file. Copy .env.example to .env and set your secrets.
  exit /b 1
)

REM Authenticate with Google Cloud
echo Authenticating with Google Cloud...
call gcloud auth configure-docker %REGION%-docker.pkg.dev --quiet
if errorlevel 1 goto :fail

REM Set the project
call gcloud config set project %PROJECT_ID%
if errorlevel 1 goto :fail

REM gcloud artifacts repositories create %REPOSITORY_NAME% --repository-format=docker --location=%REGION%

for /f "delims=" %%a in ('python scripts\get_docker_build_args.py') do set DOCKER_BUILD_ARGS=%%a

docker build --no-cache %DOCKER_BUILD_ARGS% -t %IMAGE_NAME%:%IMAGE_TAG% .
if errorlevel 1 goto :fail

docker tag %IMAGE_NAME%:%IMAGE_TAG% %REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%IMAGE_NAME%:%IMAGE_TAG%
if errorlevel 1 goto :fail

docker push %REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%IMAGE_NAME%:%IMAGE_TAG%
if errorlevel 1 goto :fail

python scripts\gcloud_env_from_dotenv.py
if errorlevel 1 goto :fail

call gcloud run deploy %SERVICE_NAME% --image %REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%IMAGE_NAME%:%IMAGE_TAG% --platform managed --region %REGION% --allow-unauthenticated --timeout=600s --min-instances=1 --memory=512Mi --concurrency=80 --cpu=1 --env-vars-file=.gcloud.env.yaml
if errorlevel 1 goto :fail

if exist .gcloud.env.yaml del .gcloud.env.yaml

echo.
echo [OK] Deploy finished. Image tag: %IMAGE_TAG%
goto :eof

:fail
if exist .gcloud.env.yaml del .gcloud.env.yaml
echo.
echo [ERROR] Deploy failed at a previous step. See output above.
exit /b 1
