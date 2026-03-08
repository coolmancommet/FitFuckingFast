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

# --- Check for Surge ---
if ! command -v surge &> /dev/null; then
    echo "Surge CLI not found. Attempting to install it..."
    if command -v brew &> /dev/null; then
        brew install surge-downloader/tap/surge
        echo "Surge has been installed."
    else
        echo "Error: Homebrew is not installed. Please install Homebrew or install Surge manually."
        echo "To install Surge manually: brew install surge-downloader/tap/surge"
        exit 1
    fi
else
    echo "Surge is already installed."
fi

# --- Install dependencies using uv ---
echo "Syncing dependencies using uv..."
uv sync

# --- Run the application ---
echo "Starting the main application with uv..."
# Execute the main script using uv, passing all command-line arguments
uv run python main.py "$@"
