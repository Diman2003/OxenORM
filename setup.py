#!/usr/bin/env python3
"""
Setup script for OxenORM CLI tool.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="oxenorm-cli",
    version="0.1.0",
    author="OxenORM Team",
    author_email="team@oxenorm.dev",
    description="Fast, async Python ORM with Rust backend - CLI Tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Diman2003/OxenORM",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyo3>=0.19.0",
        "sqlx>=0.7.0",
        "asyncpg>=0.28.0",
    ],
    entry_points={
        "console_scripts": [
            "oxen=oxen.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 