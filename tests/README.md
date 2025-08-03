# OxenORM Tests

This directory contains all test files for the OxenORM project.

## Test Organization

All test files have been moved from the root directory to this `tests/` folder for better organization.

## Running Tests

### Run All Tests
```bash
cd tests
python run_tests.py
```

### Run Specific Test
```bash
cd tests
python run_tests.py test_simple_coordination
# or
python run_tests.py test_simple_coordination.py
```

### Run Individual Test File
```bash
cd tests
python test_simple_coordination.py
```

## Test Categories

### Core Functionality Tests
- `test_simple_coordination.py` - Basic coordination between migrations and models
- `test_coordination_debug.py` - Debug coordination issues
- `test_migration_debug.py` - Debug migration system
- `test_basic_migration_working.py` - Basic migration functionality

### Comprehensive Tests
- `test_final_comprehensive.py` - Comprehensive test across all databases
- `test_final_summary.py` - Summary of all fixes working together
- `test_all_fields_comprehensive.py` - Test all field types
- `test_comprehensive_features.py` - Test advanced features
- `test_comprehensive_fixes.py` - Test all fixes

### Database-Specific Tests
- `test_sqlite_basic.py` - SQLite basic functionality
- `test_postgresql_simple.py` - PostgreSQL basic functionality
- `test_postgresql_advanced_features.py` - PostgreSQL advanced features
- `test_postgresql_extensions.py` - PostgreSQL extensions (hstore, PostGIS)
- `test_postgresql_fixed.py` - PostgreSQL fixes
- `test_postgresql_debug.py` - PostgreSQL debugging
- `test_postgresql_host.py` - PostgreSQL host connection
- `test_postgresql_simple_rust.py` - PostgreSQL with Rust backend
- `test_postgresql_advanced_rust.py` - PostgreSQL advanced with Rust

### Migration Tests
- `test_migration_schema_model_fields.py` - Migration schema generation
- `test_model_fields_simple.py` - Simple model field tests
- `test_model_fields_comprehensive.py` - Comprehensive model field tests
- `test_model_fields_fresh.py` - Fresh model field tests
- `test_model_fields_with_tables.py` - Model fields with table creation

### Rust Integration Tests
- `test_rust_backend_integration.py` - Rust backend integration
- `test_rust_debug.py` - Rust debugging
- `test_debug_rust.py` - Debug Rust integration

### Advanced Features Tests
- `test_uvloop_integration.py` - uvloop integration
- `test_file_image_fields.py` - File and image field tests
- `test_phase1_phase2.py` - Phase 1 and 2 tests
- `test_phase3_production.py` - Phase 3 production tests

## Test Database Files

The test database files (`.db` files) are also stored in this directory and are created automatically when running tests.

## Test Structure

Each test file should:
1. Import necessary modules from oxen
2. Define test models
3. Have a `main()` function that runs the test
4. Use proper error handling and cleanup

Example test structure:
```python
#!/usr/bin/env python3
import asyncio
from oxen import connect, disconnect
from oxen.models import Model
from oxen.fields import CharField

class TestModel(Model):
    name = CharField(max_length=100)

async def test_function():
    # Test implementation
    pass

async def main():
    await test_function()

if __name__ == "__main__":
    asyncio.run(main())
```

## Notes

- All tests should be run from the `tests/` directory
- Tests automatically create and clean up their own database files
- The test runner script handles importing and running tests
- Database connections are properly managed with connect/disconnect 