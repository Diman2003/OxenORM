#!/bin/bash

# Cross-platform release script for OxenORM
# This script builds and publishes wheels for Linux, Windows, and macOS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYPI_USERNAME="__token__"
PYPI_PASSWORD=""
VERSION=""
DRY_RUN=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -v, --version VERSION    Version to release (required)"
    echo "  -p, --password PASSWORD  PyPI password/token (required)"
    echo "  -d, --dry-run            Dry run (don't upload to PyPI)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 -v 0.2.0 -p your-pypi-token"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -p|--password)
            PYPI_PASSWORD="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$VERSION" ]]; then
    print_error "Version is required"
    show_usage
    exit 1
fi

if [[ "$DRY_RUN" == false && -z "$PYPI_PASSWORD" ]]; then
    print_error "PyPI password/token is required for upload"
    show_usage
    exit 1
fi

print_status "Starting cross-platform release for OxenORM v$VERSION"

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_error "pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Update version in pyproject.toml
print_status "Updating version to $VERSION in pyproject.toml"
sed -i.bak "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Clean previous builds
print_status "Cleaning previous builds"
rm -rf dist/ target/ build/ *.egg-info/

# Install build dependencies
print_status "Installing build dependencies"
pip install --upgrade build twine maturin

# Install Rust targets for cross-compilation
print_status "Installing Rust targets for cross-compilation"
rustup target add \
    x86_64-unknown-linux-gnu \
    aarch64-unknown-linux-gnu \
    x86_64-pc-windows-msvc \
    x86_64-apple-darwin \
    aarch64-apple-darwin

# Build source distribution
print_status "Building source distribution"
python -m build --sdist

# Build wheels for all platforms
print_status "Building wheels for all platforms"

# Linux x86_64
print_status "Building Linux x86_64 wheel"
maturin build --release --target x86_64-unknown-linux-gnu --out dist

# Linux aarch64
print_status "Building Linux aarch64 wheel"
maturin build --release --target aarch64-unknown-linux-gnu --out dist

# Windows x86_64
print_status "Building Windows x86_64 wheel"
maturin build --release --target x86_64-pc-windows-msvc --out dist

# macOS x86_64
print_status "Building macOS x86_64 wheel"
maturin build --release --target x86_64-apple-darwin --out dist

# macOS aarch64
print_status "Building macOS aarch64 wheel"
maturin build --release --target aarch64-apple-darwin --out dist

# List built distributions
print_status "Built distributions:"
ls -la dist/

# Check file sizes
print_status "Distribution file sizes:"
du -h dist/*

# Validate distributions
print_status "Validating distributions"
twine check dist/*

if [[ "$DRY_RUN" == true ]]; then
    print_warning "DRY RUN: Not uploading to PyPI"
    print_status "To upload, run: twine upload --username $PYPI_USERNAME --password [TOKEN] dist/*"
else
    # Upload to PyPI
    print_status "Uploading to PyPI"
    twine upload --username "$PYPI_USERNAME" --password "$PYPI_PASSWORD" dist/*
    
    print_success "Successfully uploaded to PyPI!"
    print_status "Package available at: https://pypi.org/project/oxen-orm/$VERSION/"
fi

# Test installation
print_status "Testing installation from PyPI"
pip install --upgrade oxen-orm

# Test imports
print_status "Testing imports"
python -c "import oxen; print('✅ OxenORM imported successfully')"
python -c "from oxen import Model; print('✅ Model class available')"
python -c "from oxen.cli import main; print('✅ CLI tool available')"

print_success "Cross-platform release completed successfully!"

# Show installation instructions
echo ""
echo "🎉 OxenORM v$VERSION is now available!"
echo ""
echo "Install with:"
echo "  pip install oxen-orm"
echo ""
echo "Install with optional dependencies:"
echo "  pip install oxen-orm[postgres,mysql,sqlite,admin,monitoring]"
echo ""
echo "Available for:"
echo "  ✅ Linux (x86_64, aarch64)"
echo "  ✅ Windows (x86_64)"
echo "  ✅ macOS (x86_64, aarch64)"
echo ""
echo "PyPI URL: https://pypi.org/project/oxen-orm/$VERSION/" 