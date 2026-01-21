#!/bin/bash

APP_VERSION="1.0"
APP_NAME="pagamov_bot"

docker build -t ${APP_NAME}:${APP_VERSION} .

docker run -d \
  --name ${APP_NAME}-${APP_VERSION} \
  ${APP_NAME}:${APP_VERSION}

docker image ls ${APP_NAME}

docker ps --filter "name=${APP_NAME}_${APP_VERSION}"