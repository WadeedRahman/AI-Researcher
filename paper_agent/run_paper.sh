#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get the project root directory (parent of paper_agent)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment variables from .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY is not set."
    echo "Please set it in one of the following ways:"
    echo "  1. Export it: export OPENAI_API_KEY=your_key_here"
    echo "  2. Add it to $PROJECT_ROOT/.env file: OPENAI_API_KEY=your_key_here"
    exit 1
fi

# Export the API key for the Python script
export OPENAI_API_KEY

# Configuration
research_field=vq
instance_id=rotated_vq

# Run the Python script
python "$SCRIPT_DIR/writing.py" --research_field "${research_field}" --instance_id "${instance_id}"