#!/usr/bin/env python3
"""
Build script for OxenORM

This script helps with building the Rust backend and managing the development environment.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def check_rust():
    """Check if Rust is installed."""
    result = run_command("rustc --version", check=False)
    if result.returncode != 0:
        print("Rust is not installed. Please install Rust first:")
        print("curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
        sys.exit(1)
    print(f"Rust version: {result.stdout.strip()}")


def check_maturin():
    """Check if maturin is installed."""
    result = run_command("maturin --version", check=False)
    if result.returncode != 0:
        print("Maturin is not installed. Installing...")
        run_command("pip install maturin")
    print(f"Maturin version: {result.stdout.strip()}")


def build_rust():
    """Build the Rust backend."""
    print("Building Rust backend...")
    run_command("maturin build --release")


def develop_rust():
    """Build Rust backend in development mode."""
    print("Building Rust backend in development mode...")
    run_command("maturin develop --release")


def test_python():
    """Run Python tests."""
    print("Running Python tests...")
    run_command("python -m pytest tests/ -v")


def test_rust():
    """Run Rust tests."""
    print("Running Rust tests...")
    run_command("cargo test")


def clean():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    run_command("cargo clean")
    run_command("rm -rf target/")
    run_command("rm -rf dist/")
    run_command("rm -rf build/")


def install_dev():
    """Install development dependencies."""
    print("Installing development dependencies...")
    run_command("pip install -e '.[dev]'")


def format_code():
    """Format code using rustfmt and black."""
    print("Formatting Rust code...")
    run_command("cargo fmt")
    
    print("Formatting Python code...")
    run_command("black oxen/ tests/ examples/")


def lint():
    """Run linters."""
    print("Running Rust linter...")
    run_command("cargo clippy -- -D warnings")
    
    print("Running Python linter...")
    run_command("ruff check oxen/ tests/ examples/")


def check_types():
    """Run type checking."""
    print("Running Python type checking...")
    run_command("mypy oxen/")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="OxenORM build script")
    parser.add_argument(
        "command",
        choices=[
            "check", "build", "develop", "test", "test-python", "test-rust",
            "clean", "install-dev", "format", "lint", "check-types", "all"
        ],
        help="Command to run"
    )
    
    args = parser.parse_args()
    
    if args.command == "check":
        check_rust()
        check_maturin()
    
    elif args.command == "build":
        check_rust()
        check_maturin()
        build_rust()
    
    elif args.command == "develop":
        check_rust()
        check_maturin()
        develop_rust()
    
    elif args.command == "test":
        test_python()
        test_rust()
    
    elif args.command == "test-python":
        test_python()
    
    elif args.command == "test-rust":
        test_rust()
    
    elif args.command == "clean":
        clean()
    
    elif args.command == "install-dev":
        install_dev()
    
    elif args.command == "format":
        format_code()
    
    elif args.command == "lint":
        lint()
    
    elif args.command == "check-types":
        check_types()
    
    elif args.command == "all":
        check_rust()
        check_maturin()
        install_dev()
        develop_rust()
        format_code()
        lint()
        check_types()
        test_python()
        test_rust()
    
    print("Done!")


if __name__ == "__main__":
    main() 