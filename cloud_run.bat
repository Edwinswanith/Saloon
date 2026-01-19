@echo off
set PROJECT_ID=legel-assistent-466812
set REPOSITORY_NAME=saloon
set REGION=europe-west2
set IMAGE_NAME=saloon-management-system
set IMAGE_TAG=v11
set SERVICE_NAME=saloon-management-system

REM Authenticate with Google Cloud
echo Authenticating with Google Cloud...
gcloud auth configure-docker %REGION%-docker.pkg.dev --quiet

REM Set the project
gcloud config set project %PROJECT_ID%

REM gcloud artifacts repositories create %REPOSITORY_NAME% --repository-format=docker --location=%REGION%

docker build --no-cache -t %IMAGE_NAME%:%IMAGE_TAG% .

docker tag %IMAGE_NAME%:%IMAGE_TAG% %REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%IMAGE_NAME%:%IMAGE_TAG%

docker push %REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%IMAGE_NAME%:%IMAGE_TAG%

gcloud run deploy %SERVICE_NAME% --image %REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%IMAGE_NAME%:%IMAGE_TAG% --platform managed --region %REGION% --allow-unauthenticated --timeout=600s
