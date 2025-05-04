#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define variables
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# Create a virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv $VENV_DIR
else
    echo "Virtual environment already exists in $VENV_DIR."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r $REQUIREMENTS_FILE
else
    echo "No $REQUIREMENTS_FILE found. Skipping dependency installation."
fi

# Print success message
echo "Setup complete. Virtual environment is ready."