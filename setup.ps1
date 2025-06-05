# Quick Setup Script (Windows)

# This script checks for Python 3 and pip, creates/activates a virtual environment,
# upgrades pip, and installs the required packages from requirements.txt.
# Usage: .\setup.ps1

$ErrorActionPreference = "Stop"

# Check for Python
try {
    python.exe --version > $null 2>&1
} catch {
    Write-Host "Python 3 is not installed or not in PATH. Install Python 3.7+ and add it to PATH." -ForegroundColor Red
    exit 1
}

# Check for pip
try {
    pip --version > $null 2>&1
} catch {
    Write-Host "pip is not available. Reinstall Python with pip included." -ForegroundColor Red
    exit 1
}

# Create a local Python environment (if it doesn't already exist)
if (Test-Path -Path "venv") {
    Write-Host "Virtual environment already exists. Skipping creation." -ForegroundColor Yellow
} else {
    Write-Host "Creating a local virtual Python environment..." -ForegroundColor Cyan
    python.exe -m venv --copies venv
}

# Activate the Python environment
Write-Host "Activating environment..." -ForegroundColor Cyan
venv\Scripts\Activate.ps1

# Update PIP before installing packages
Write-Host "Upgrading PIP to its latest version..." -ForegroundColor Cyan
python.exe -m pip install --upgrade pip

# Install required packages
Write-Host "Installing required project packages..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Setup complete" -ForegroundColor Green
