#!/bin/bash

# Security First: Prevent root execution
if [ "$EUID" -eq 0 ]; then 
  echo "ERROR: Please do not run as root."
  exit 1
fi

echo "[*] Initializing Zero-Touch Environment..."

VENV_DIR="portapack_updater_env"

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 required."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "[*] Installing dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "ERROR: requirements.txt missing."
    exit 1
fi

echo ""
echo "SETUP COMPLETE."
echo "To run the auto-updater:"
echo "source $VENV_DIR/bin/activate"
echo "python3 hakcRF.py"
echo ""