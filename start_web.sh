#!/usr/bin/env bash
# ==============================================================================
# macOS AI Agent — Web Dashboard Launcher
# Starts FastAPI server and hosts the modern cyber-glassmorphism web UI.
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 Starting macOS AI Agent Web Server..."
echo "🌐 Open your browser at: http://localhost:8000"
echo "Press Ctrl+C to stop the server."
echo ""

python server.py
