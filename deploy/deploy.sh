#!/usr/bin/env bash
# Deployment script for Corpus Backend on Contabo VPS

set -e

APP_DIR="/var/www/corpus-backend"

echo "==> Deploying Corpus Backend in $APP_DIR"
cd "$APP_DIR"

if [ ! -d ".venv" ]; then
    echo "==> Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "==> Activating virtual environment & installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "==> Creating .env from .env.example (Make sure to fill in GEMINI_API_KEY!)..."
    cp .env.example .env
fi

echo "==> Restarting systemd service..."
sudo systemctl daemon-reload
sudo systemctl restart corpus.service
sudo systemctl status corpus.service --no-pager

echo "==> Deployment completed successfully!"
