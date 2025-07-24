#!/bin/bash

# OxenORM Development Environment Setup Script

set -e

echo "🐂 OxenORM Development Environment Setup"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "oxenorm_env" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv oxenorm_env
    echo "✅ Virtual environment created: oxenorm_env"
else
    echo "✅ Virtual environment already exists: oxenorm_env"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source oxenorm_env/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Check Rust installation
echo "🔍 Checking Rust installation..."
if command -v cargo &> /dev/null; then
    echo "✅ Rust is installed"
    cargo --version
else
    echo "❌ Rust is not installed"
    echo "Please install Rust: https://rustup.rs/"
    exit 1
fi

# Test Python components
echo "🧪 Testing Python components..."
python3 test_oxenorm_basic.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate environment: source oxenorm_env/bin/activate"
echo "2. Fix Rust PyO3 integration issues"
echo "3. Build Rust backend: cargo build"
echo "4. Run integration tests: python3 test_integration.py"
echo ""
echo "Happy coding! 🚀" 