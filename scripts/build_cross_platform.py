#!/usr/bin/env python3
"""
Cross-platform build script for OxenORM

This script builds wheels for multiple platforms:
- Linux (x86_64, aarch64)
- Windows (x86_64)
- macOS (x86_64, aarch64)
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import argparse


def run_command(cmd, cwd=None, env=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        return False
    
    return True


def get_rust_targets():
    """Get the list of Rust targets to build for."""
    targets = []
    
    # Linux targets
    targets.extend([
        "x86_64-unknown-linux-gnu",
        "aarch64-unknown-linux-gnu"
    ])
    
    # Windows targets
    targets.extend([
        "x86_64-pc-windows-msvc"
    ])
    
    # macOS targets
    targets.extend([
        "x86_64-apple-darwin",
        "aarch64-apple-darwin"
    ])
    
    return targets


def install_rust_targets():
    """Install Rust targets for cross-compilation."""
    targets = get_rust_targets()
    
    for target in targets:
        print(f"Installing Rust target: {target}")
        if not run_command(["rustup", "target", "add", target]):
            print(f"Failed to install target {target}")
            return False
    
    return True


def build_wheel(target, out_dir="dist"):
    """Build a wheel for a specific target."""
    print(f"\nBuilding wheel for target: {target}")
    
    # Create output directory
    os.makedirs(out_dir, exist_ok=True)
    
    # Build command
    cmd = [
        "maturin", "build",
        "--release",
        "--target", target,
        "--out", out_dir
    ]
    
    return run_command(cmd)


def build_all_wheels():
    """Build wheels for all targets."""
    targets = get_rust_targets()
    
    print("Building wheels for all targets...")
    print(f"Targets: {targets}")
    
    # Install Rust targets
    if not install_rust_targets():
        print("Failed to install Rust targets")
        return False
    
    # Build wheels
    success_count = 0
    for target in targets:
        if build_wheel(target):
            success_count += 1
            print(f"✅ Successfully built wheel for {target}")
        else:
            print(f"❌ Failed to build wheel for {target}")
    
    print(f"\nBuild Summary:")
    print(f"Successful builds: {success_count}/{len(targets)}")
    
    return success_count == len(targets)


def build_source_distribution():
    """Build source distribution."""
    print("\nBuilding source distribution...")
    
    cmd = ["python", "-m", "build", "--sdist"]
    return run_command(cmd)


def upload_to_pypi(username, password, dist_dir="dist"):
    """Upload distributions to PyPI."""
    print(f"\nUploading to PyPI...")
    
    # Check if files exist
    dist_path = Path(dist_dir)
    if not dist_path.exists():
        print(f"Distribution directory {dist_dir} does not exist")
        return False
    
    # List files to upload
    files = list(dist_path.glob("*.whl")) + list(dist_path.glob("*.tar.gz"))
    if not files:
        print("No distribution files found")
        return False
    
    print(f"Found {len(files)} files to upload:")
    for file in files:
        print(f"  {file}")
    
    # Upload command
    cmd = [
        "twine", "upload",
        "--username", username,
        "--password", password
    ] + [str(f) for f in files]
    
    return run_command(cmd)


def test_installation():
    """Test installation from PyPI."""
    print("\nTesting installation...")
    
    # Install from PyPI
    if not run_command(["pip", "install", "--upgrade", "oxen-orm"]):
        print("Failed to install from PyPI")
        return False
    
    # Test imports
    test_commands = [
        "import oxen; print('✅ OxenORM imported successfully')",
        "from oxen import Model; print('✅ Model class available')",
        "from oxen.cli import main; print('✅ CLI tool available')"
    ]
    
    for cmd in test_commands:
        if not run_command(["python", "-c", cmd]):
            print(f"Failed to test: {cmd}")
            return False
    
    print("✅ All installation tests passed!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Cross-platform build script for OxenORM")
    parser.add_argument("--build-wheels", action="store_true", help="Build wheels for all platforms")
    parser.add_argument("--build-source", action="store_true", help="Build source distribution")
    parser.add_argument("--upload", action="store_true", help="Upload to PyPI")
    parser.add_argument("--test", action="store_true", help="Test installation from PyPI")
    parser.add_argument("--username", default="__token__", help="PyPI username")
    parser.add_argument("--password", help="PyPI password/token")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    
    args = parser.parse_args()
    
    if args.all:
        args.build_wheels = True
        args.build_source = True
        args.upload = True
        args.test = True
    
    success = True
    
    if args.build_wheels:
        print("🚀 Building wheels for all platforms...")
        if not build_all_wheels():
            success = False
            print("❌ Wheel building failed")
    
    if args.build_source:
        print("📦 Building source distribution...")
        if not build_source_distribution():
            success = False
            print("❌ Source distribution building failed")
    
    if args.upload:
        if not args.password:
            print("❌ Password/token required for upload")
            success = False
        else:
            print("📤 Uploading to PyPI...")
            if not upload_to_pypi(args.username, args.password):
                success = False
                print("❌ Upload failed")
    
    if args.test:
        print("🧪 Testing installation...")
        if not test_installation():
            success = False
            print("❌ Installation test failed")
    
    if success:
        print("\n🎉 All operations completed successfully!")
    else:
        print("\n❌ Some operations failed")
        sys.exit(1)


if __name__ == "__main__":
    main() 