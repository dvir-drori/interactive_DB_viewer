#!/usr/bin/env bash
# build.sh
# Render build script — runs once before the server starts.
# Installs Node.js, builds the React frontend, then installs Python packages.

set -e  # exit immediately on any error

echo "=== [1/3] Installing Node.js ==="
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

echo "=== [2/3] Building React frontend ==="
cd frontend
npm install
npm run build      # outputs to backend/static/ (per vite.config.js)
cd ..

echo "=== [3/3] Installing Python packages ==="
pip install -r backend/requirements.txt

echo "=== Build complete ==="
