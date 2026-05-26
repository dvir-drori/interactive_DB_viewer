#!/usr/bin/env bash
# build.sh
# Render build script — runs once before the server starts.
# Downloads Node.js binary, builds the React frontend, then installs Python packages.

set -e  # exit immediately on any error

echo "=== [1/3] Installing Node.js ==="
NODE_VERSION=20.11.1
curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" | tar -xJ
export PATH="$(pwd)/node-v${NODE_VERSION}-linux-x64/bin:$PATH"
echo "Node $(node --version) / npm $(npm --version)"

echo "=== [2/3] Building React frontend ==="
cd frontend
npm ci              # clean install from lockfile for reproducible builds
npm run build       # outputs to backend/static/ (per vite.config.js)
cd ..

echo "=== [3/3] Installing Python packages ==="
pip install -r backend/requirements.txt

echo "=== Build complete ==="
