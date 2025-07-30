#!/usr/bin/env python3
"""
Setup script for OxenORM.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="oxen-orm",
    version="0.1.0",
    author="OxenORM Team",
    author_email="team@oxenorm.dev",
    description="High-performance Python ORM backed by Rust - 15× faster than SQLAlchemy",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0",
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "oxen=oxen.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 