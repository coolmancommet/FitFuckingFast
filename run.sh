#!/bin/bash
set -e

# --- Check for uv ---
if ! command -v uv &> /dev/null; then
    echo "uv not found. Attempting to install it..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # The installer script will add uv to the path, but we need to source the environment file for the current session.
    source "$HOME/.cargo/env"
    echo "uv has been installed."
else
    echo "uv is already installed."
fi

# --- Check for aria2c ---
if ! command -v aria2c &> /dev/null; then
    echo "Error: aria2c is not installed. Please install it using your system's package manager (e.g., 'sudo apt-get install aria2' or 'brew install aria2')."
    exit 1
fi

# --- Install dependencies using uv ---
echo "Syncing dependencies using uv..."
uv sync

# --- Run the application ---
echo "Starting aria2c daemon..."
aria2c --enable-rpc --rpc-listen-all=true --rpc-allow-origin-all &
# Store the process ID of the background job
aria2_pid=$!

# Ensure aria2c is terminated when the script exits
trap "echo 'Stopping aria2c daemon...'; kill $aria2_pid" EXIT

# Wait a moment for the server to start
sleep 2

echo "Starting the main application with uv..."
# Execute the main script using uv, passing all command-line arguments
uv run python main.py "$@"
