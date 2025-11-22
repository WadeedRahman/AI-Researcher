#!/bin/bash
# Script to run AI-Researcher Docker container

# Check if container already exists
if [ "$(docker ps -aq -f name=airesearcher)" ]; then
    echo "Container 'airesearcher' already exists."
    echo "Stopping and removing existing container..."
    docker stop airesearcher
    docker rm airesearcher
fi

# Check if GPU is available
GPU_FLAG=""
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Adding --gpus all flag."
    GPU_FLAG="--gpus all"
fi

# Run the container
echo "Starting AI-Researcher container..."
docker run -d \
  -p 8000:8000 \
  --name airesearcher \
  $GPU_FLAG \
  tjbtech1/airesearcher:v1

if [ $? -eq 0 ]; then
    echo "Container started successfully!"
    echo "View logs with: docker logs -f airesearcher"
    echo "Stop container with: docker stop airesearcher"
else
    echo "Failed to start container. Check if image exists:"
    echo "  docker pull tjbtech1/airesearcher:v1"
fi
