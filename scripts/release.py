#!/usr/bin/env python3
"""
OxenORM Release Script

Automates the release process for OxenORM.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

def run_command(command, check=True, capture_output=False):
    """Run a shell command."""
    print(f"🔄 Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=capture_output, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {command}")
        sys.exit(1)
    return result

def get_current_version():
    """Get current version from pyproject.toml."""
    with open("pyproject.toml", "r") as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if match:
            return match.group(1)
    raise ValueError("Could not find version in pyproject.toml")

def update_version(new_version):
    """Update version in pyproject.toml."""
    with open("pyproject.toml", "r") as f:
        content = f.read()
    
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    
    with open("pyproject.toml", "w") as f:
        f.write(content)
    
    print(f"✅ Updated version to {new_version}")

def update_changelog(version):
    """Update changelog with release date."""
    with open("CHANGELOG.md", "r") as f:
        content = f.read()
    
    today = datetime.now().strftime("%Y-%m-%d")
    content = content.replace("2025-01-XX", today)
    
    with open("CHANGELOG.md", "w") as f:
        f.write(content)
    
    print(f"✅ Updated changelog with release date: {today}")

def check_git_status():
    """Check if git repository is clean."""
    result = run_command("git status --porcelain", capture_output=True)
    if result.stdout.strip():
        print("❌ Git repository is not clean. Please commit all changes first.")
        print("Uncommitted changes:")
        print(result.stdout)
        sys.exit(1)
    print("✅ Git repository is clean")

def run_tests():
    """Run all tests."""
    print("🧪 Running tests...")
    run_command("python -m pytest tests/ -v")
    run_command("python test_phase3_production.py")
    print("✅ All tests passed")

def build_package():
    """Build the package."""
    print("🔨 Building package...")
    run_command("pip install maturin build twine")
    run_command("maturin build --release --out dist")
    run_command("python -m build")
    print("✅ Package built successfully")

def check_package():
    """Check the built package."""
    print("🔍 Checking package...")
    run_command("twine check dist/*")
    print("✅ Package check passed")

def create_git_tag(version):
    """Create and push git tag."""
    print(f"🏷️ Creating git tag v{version}...")
    run_command(f"git tag -a v{version} -m 'Release v{version}'")
    run_command("git push origin --tags")
    print(f"✅ Git tag v{version} created and pushed")

def main():
    """Main release process."""
    print("🚀 OxenORM Release Process")
    print("=" * 50)
    
    # Get current version
    current_version = get_current_version()
    print(f"📦 Current version: {current_version}")
    
    # Check if we want to update version
    update_version_input = input("Do you want to update the version? (y/N): ").strip().lower()
    if update_version_input == 'y':
        new_version = input(f"Enter new version (current: {current_version}): ").strip()
        if new_version:
            update_version(new_version)
            current_version = new_version
    
    # Update changelog
    update_changelog(current_version)
    
    # Check git status
    check_git_status()
    
    # Run tests
    run_tests()
    
    # Build package
    build_package()
    
    # Check package
    check_package()
    
    # Ask for confirmation before creating tag
    create_tag = input(f"Create git tag v{current_version}? (y/N): ").strip().lower()
    if create_tag == 'y':
        create_git_tag(current_version)
    
    print("\n🎉 Release process completed!")
    print(f"📦 Version: {current_version}")
    print("📁 Built packages are in the 'dist/' directory")
    print("\nNext steps:")
    print("1. Review the built packages in dist/")
    print("2. Test the package locally: pip install dist/oxen_orm-*.whl")
    print("3. Upload to PyPI: twine upload dist/*")
    print("4. Create a GitHub release")
    print("5. Share the release on social media")

if __name__ == "__main__":
    main() 