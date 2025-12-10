#!/bin/bash
# Build Docker images with git SHA tags using Pants
# Usage: ./scripts/build-docker.sh [service-name]
# Example: ./scripts/build-docker.sh auth

set -e

# Get git SHA (short version)
GIT_SHA=$(git rev-parse --short HEAD)

# Export for Pants to use
export GIT_SHA

# If service name provided, build only that service
if [ -n "$1" ]; then
    SERVICE=$1
    echo "Building ${SERVICE} service Docker image with git SHA: ${GIT_SHA}"
    pants package "services/${SERVICE}:${SERVICE}-image"
else
    echo "Building all Docker images with git SHA: ${GIT_SHA}"
    pants package services/auth:auth-image services/accounts:accounts-image
fi

echo "Build complete! Images tagged with: latest, ${GIT_SHA}"

