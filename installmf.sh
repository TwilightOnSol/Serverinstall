#!/bin/bash

# Exit on any error
set -e

echo "Updating package lists..."
sudo apt-get update

echo "Installing Python 3 and pip..."
sudo apt-get install -y python3 python3-pip

echo "Installing Google Chrome..."
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y
rm google-chrome-stable_current_amd64.deb

echo "Installing Python dependencies..."
pip3 install --user selenium webdriver-manager requests

echo "Creating screenshots directory..."
mkdir -p screenshots

echo "Installation complete! You can now run the tracker with: python3 tracker.py"