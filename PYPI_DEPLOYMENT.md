# PyPI Deployment Guide

## Overview

OxenORM is configured for automatic deployment to PyPI using GitHub Actions. The deployment is triggered when a new release is created on GitHub.

## ✅ **DEPLOYMENT SUCCESSFUL!**

**Package Name**: `oxen-orm`  
**Version**: `0.1.0`  
**PyPI URL**: https://pypi.org/project/oxen-orm/0.1.0/  
**Install Command**: `pip install oxen-orm`

## Automatic Deployment

### How it works:

1. **Release Creation**: When you create a new release on GitHub, it automatically triggers the deployment workflow
2. **GitHub Actions**: The workflow builds the package and uploads it to PyPI
3. **PyPI Token**: Uses a PyPI API token stored in GitHub Secrets

### Setup Required:

1. **PyPI Account**: Create an account on [PyPI](https://pypi.org)
2. **API Token**: Generate an API token in your PyPI account settings
3. **GitHub Secrets**: Add the token to your GitHub repository secrets

### Steps to Deploy:

1. **Create PyPI API Token**:
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Copy the token value

2. **Add to GitHub Secrets**:
   - Go to your GitHub repository
   - Navigate to Settings → Secrets and variables → Actions
   - Create a new secret named `PYPI_API_TOKEN`
   - Paste your PyPI API token

3. **Create a Release**:
   - Go to your GitHub repository
   - Click "Releases" → "Create a new release"
   - Tag version (e.g., `v0.1.0`)
   - Add release title and description
   - Publish the release

4. **Monitor Deployment**:
   - Check the Actions tab in your GitHub repository
   - The "Publish to PyPI" workflow will run automatically
   - Monitor for any errors

## Manual Deployment

If you prefer to deploy manually:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to PyPI (replace with your credentials)
twine upload dist/*
```

## Package Configuration

The package is configured in:
- `pyproject.toml`: Main package configuration
- `setup.py`: Alternative setup configuration
- `MANIFEST.in`: Files to include in the package

## Current Status

✅ **Package Configuration**: Complete
✅ **GitHub Actions**: Configured
✅ **Build System**: Working
✅ **Local Build**: Successful
✅ **PyPI Upload**: **SUCCESSFUL**
✅ **Package Available**: https://pypi.org/project/oxen-orm/0.1.0/

## Installation

Users can now install the package using:

```bash
pip install oxen-orm
```

## Next Steps

1. Set up PyPI API token in GitHub Secrets for automatic deployment
2. Create a GitHub release to trigger automatic deployment
3. Monitor the deployment process
4. Verify the package appears on PyPI

## Troubleshooting

### Common Issues:

1. **Build Failures**: Check that all dependencies are properly configured
2. **Upload Failures**: Verify PyPI API token is correct
3. **Version Conflicts**: Ensure version numbers are unique

### Debug Commands:

```bash
# Test build locally
python -m build

# Check package contents
tar -tzf dist/oxen_orm-*.tar.gz

# Validate package
twine check dist/*
```

## Package Information

- **Name**: `oxen-orm`
- **Version**: `0.1.0`
- **Description**: High-performance Python ORM backed by Rust
- **Dependencies**: pydantic, typing-extensions, click
- **Python Versions**: 3.9+
- **PyPI URL**: https://pypi.org/project/oxen-orm/0.1.0/ 