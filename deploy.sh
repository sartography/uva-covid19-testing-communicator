#!/bin/bash

#########################################################################
# Builds the Docker image for the current git branch on Travis CI and
# publishes it to Docker Hub.
#
# Parameters:
# $1: Docker Hub repository to publish to
#
# Required environment variables (place in Settings menu on Travis CI):
# $DOCKER_USERNAME: Docker Hub username
# $DOCKER_TOKEN: Docker Hub access token
#########################################################################

echo 'Building Docker image...'
DOCKER_REPO="$1"

function branch_to_tag () {
  if [ "$1" == "master" ]; then echo "latest"; else echo "$1" ; fi
}

DOCKER_TAG=$(branch_to_tag "$TRAVIS_BRANCH")

echo "DOCKER_REPO = $DOCKER_REPO"
echo "DOCKER_TAG = $DOCKER_TAG"

echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USERNAME" --password-stdin || exit 1
docker build -f Dockerfile -t "$DOCKER_REPO:$DOCKER_TAG" . || exit 1


# Push Docker image to Docker Hub
echo "Publishing to Docker Hub..."
docker push "$DOCKER_REPO" || exit 1
echo "Done."
