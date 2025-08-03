"""
Tests package for OxenORM
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import oxen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import oxen modules
try:
    from oxen import connect, disconnect
    from oxen.models import Model
    from oxen.fields import *
    from oxen.migrations import *
except ImportError as e:
    print(f"Warning: Could not import oxen modules: {e}")
    print("Make sure you're running tests from the project root directory") 