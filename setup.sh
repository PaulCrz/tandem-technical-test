#!/bin/bash

# Quick Setup Script (Linux / macOS)

# This script checks for Python 3 and pip, creates/activates a virtual environment,
# upgrades pip, and installs the required packages from requirements.txt.
# Usage: chmod +x setup.sh && ./setup.sh

set -e  # Exit immediately if a command exits with a non-zero status

# ANSI color codes
RED="\033[0;31m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
GREEN="\033[0;32m"
RESET="\033[0m"

# Create a local Python virtual environment (if it doesn't already exist)
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping creation.${RESET}"
else
    echo -e "${CYAN}Creating a local virtual Python environment...${RESET}"
    python3 -m venv venv
fi

# Activate the Python environment
echo -e "${CYAN}Activating environment...${RESET}"
# shellcheck disable=SC1091
source venv/bin/activate

# Upgrade pip to its latest version
echo -e "${CYAN}Upgrading pip to its latest version...${RESET}"
pip install --upgrade pip

# Install required packages
if [ -f "requirements.txt" ]; then
    echo -e "${CYAN}Installing required project packages from requirements.txt...${RESET}"
    pip install -r requirements.txt
else
    echo -e "${YELLOW}requirements.txt not found. Skipping package installation.${RESET}"
fi

echo -e "${GREEN}Setup complete.${RESET}"
