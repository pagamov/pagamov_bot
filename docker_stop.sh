#!/bin/bash

APP_VERSION="1.0"
APP_NAME="pagamov_bot"

CONTAINER_ID=$(docker ps -a --filter "ancestor=${APP_NAME}:${APP_VERSION}" --format "{{.ID}}")

if [ -n "$CONTAINER_ID" ]; then
    echo "Stopping container $CONTAINER_ID..."
    docker stop "$CONTAINER_ID"
    echo "Removing container $CONTAINER_ID..."
    docker rm "$CONTAINER_ID"
fi

# Remove the image
IMAGE_ID=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep ${APP_NAME}:${APP_VERSION})

if [ -n "$IMAGE_ID" ]; then
    echo "Removing image $IMAGE_ID..."
    docker rmi "$IMAGE_ID"
fi