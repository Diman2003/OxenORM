#!/bin/bash

set -e

echo "🚀 Setting up OxenORM development environment..."

# Check if Python 3.9+ is available
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed. Please install Rust from https://rustup.rs/"
    exit 1
fi

echo "✅ Rust is installed"

# Create virtual environment if it doesn't exist
if [ ! -d "oxenorm_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv oxenorm_env
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source oxenorm_env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "📚 Installing development dependencies..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

# Build Rust extension
echo "🔨 Building Rust extension..."
maturin develop --release

echo "✅ Development environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source oxenorm_env/bin/activate"
echo ""
echo "To run tests:"
echo "  make test"
echo ""
echo "To run linting:"
echo "  make lint"
echo ""
echo "To format code:"
echo "  make format" 