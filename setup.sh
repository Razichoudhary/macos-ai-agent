#!/usr/bin/env bash
# ==============================================================================
# MacOS AI Agent — Quick Setup Script
# Automatically creates virtual environment, installs dependencies,
# and prepares the .env file.
# ==============================================================================

set -e

echo "🤖 Setting up MacOS AI Agent..."

# 1. Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+ from python.org or via Homebrew."
    exit 1
fi

# 2. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment (venv)..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists."
fi

# 3. Activate venv
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# 4. Upgrade pip and install dependencies
echo "📥 Installing required dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 5. Prepare .env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please open .env and add your free Google Gemini API Key:"
    echo "    1. Get your free key at: https://aistudio.google.com/"
    echo "    2. Edit .env and paste: GEMINI_API_KEY=your_key_here"
    echo ""
else
    echo "✅ .env file already exists."
fi

echo "✨ Setup complete!"
echo ""
echo "🚀 To launch the agent, run:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
