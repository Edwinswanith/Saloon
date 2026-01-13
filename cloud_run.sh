#!/bin/bash
PROJECT_ID=legel-assistent-466812
REPOSITORY_NAME=saloon
REGION=europe-west2
IMAGE_NAME=saloon-management-system
IMAGE_TAG=v05
SERVICE_NAME=saloon-management-system

# Authenticate with Google Cloud
echo "Authenticating with Google Cloud..."
gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

# Set the project
gcloud config set project $PROJECT_ID

# gcloud artifacts repositories create $REPOSITORY_NAME --repository-format=docker --location=$REGION

docker build --no-cache -t $IMAGE_NAME:$IMAGE_TAG .

docker tag $IMAGE_NAME:$IMAGE_TAG $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/$IMAGE_NAME:$IMAGE_TAG

docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/$IMAGE_NAME:$IMAGE_TAG

gcloud run deploy $SERVICE_NAME --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/$IMAGE_NAME:$IMAGE_TAG --platform managed --region $REGION --allow-unauthenticated --timeout=600s

