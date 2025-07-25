# OxenORM Enhanced Migration System

The OxenORM Enhanced Migration System provides a comprehensive solution for managing database schema changes with advanced features including automatic migration generation, rollback capabilities, multi-database support, and safety checks.

## 🚀 Features

### Core Features
- **Automatic Migration Generation**: Generate migrations from model changes
- **Schema Comparison**: Compare database schemas and generate diffs
- **Migration Rollback**: Rollback migrations with dependency resolution
- **Multi-Database Support**: Manage migrations across different database types
- **Transaction Management**: Execute migrations within transactions
- **Safety Checks**: Validate migrations for dangerous operations
- **Dry-Run Mode**: Preview migration execution without applying changes

### Advanced Features
- **Dependency Resolution**: Handle complex migration dependencies
- **Migration Templates**: Customizable SQL templates for common operations
- **Progress Tracking**: Monitor migration execution progress
- **Validation System**: Comprehensive migration validation
- **Schema Inspection**: Analyze current database schema
- **Migration History**: Track migration execution history

## 📦 Installation

The enhanced migration system is included with OxenORM. No additional installation is required.

## 🛠️ Usage

### Basic Migration Commands

#### Generate Migrations

```bash
# Generate migration from model changes
oxen migrate makemigrations "Add user table"

# Generate initial migration from models
oxen migrate makemigrations "Initial migration" --initial --models User Category Post

# Generate migration with custom author
oxen migrate makemigrations "Add email field" --author "john.doe@example.com"
```

#### Execute Migrations

```bash
# Run all pending migrations
oxen migrate run

# Run migrations up to specific version
oxen migrate run --target 20231201120000

# Dry run (preview without executing)
oxen migrate run --dry-run
```

#### Rollback Migrations

```bash
# Rollback to specific version
oxen migrate rollback 20231201120000

# Preview rollback plan
oxen migrate rollback-plan 20231201120000

# Dry run rollback
oxen migrate rollback 20231201120000 --dry-run
```

#### Migration Management

```bash
# Show migration status
oxen migrate status

# Show migration history
oxen migrate history --limit 20

# Show execution plan
oxen migrate plan --target 20231201120000

# Validate migrations
oxen migrate validate

# Safety check
oxen migrate safety-check
```

#### Schema Management

```bash
# Show current database schema
oxen migrate schema show

# Generate SQL from models
oxen migrate schema generate --models User Category Post
```

### Programmatic Usage

#### Basic Migration Engine

```python
from oxen.migrations.enhanced_engine import EnhancedMigrationEngine, MigrationConfig
from oxen.multi_db_engine import MultiDbEngine

# Initialize engine
engine = MultiDbEngine("postgresql://user:pass@localhost/db")
await engine.connect()

# Configure migration engine
config = MigrationConfig(
    migrations_dir="migrations",
    validate_before_run=True,
    use_transactions=True
)

migration_engine = EnhancedMigrationEngine(engine, config)

# Generate migration
migration = await migration_engine.makemigrations(
    models=[User, Category, Post],
    description="Add blog models",
    author="developer"
)

# Execute migrations
result = await migration_engine.migrate()
print(f"Executed {len(result.migrations_executed)} migrations")

# Rollback migrations
result = await migration_engine.migrate_rollback("20231201120000")
print(f"Rolled back {len(result.migrations_executed)} migrations")
```

#### Multi-Database Support

```python
# Add multiple databases
migration_engine.add_database("postgres", postgres_engine, config)
migration_engine.add_database("mysql", mysql_engine, config)
migration_engine.add_database("sqlite", sqlite_engine, config)

# Switch between databases
migration_engine.switch_database("postgres")
await migration_engine.migrate()

migration_engine.switch_database("mysql")
await migration_engine.migrate()

# Migrate all databases
results = await migration_engine.migrate_all_databases()
for db_name, result in results.items():
    print(f"{db_name}: {len(result.migrations_executed)} migrations executed")
```

#### Schema Management

```python
# Get current schema
schema = await migration_engine.get_current_schema()
print(f"Database has {len(schema)} tables")

# Compare schemas
old_schema = {...}  # Previous schema
new_schema = {...}  # Current schema
diff = await migration_engine.compare_schemas(old_schema, new_schema)

if diff.has_changes():
    print(f"Changes detected: {diff.get_summary()}")

# Generate SQL from models
sql = await migration_engine.generate_schema_sql([User, Category, Post])
print("Generated SQL:", sql)
```

#### Migration Validation

```python
# Validate migration
validation = await migration_engine.validate_migration(migration)
if not validation['is_valid']:
    print("Migration validation failed:", validation['errors'])

# Safety check
safety = await migration_engine.check_migration_safety(migration)
if not safety['is_safe']:
    print("Dangerous operations detected:", safety['dangerous_operations'])

# Validate all migrations
all_validations = await migration_engine.validate_all_migrations()
for filepath, validation in all_validations.items():
    print(f"{filepath}: {'Valid' if validation['is_valid'] else 'Invalid'}")
```

## 📋 Migration File Format

Migrations are stored as JSON files with the following structure:

```json
{
  "id": "20231201120000_abc12345",
  "name": "20231201120000_add_user_table",
  "version": "20231201120000",
  "up_sql": "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100));",
  "down_sql": "DROP TABLE users;",
  "description": "Add user table",
  "author": "developer",
  "created_at": "2023-12-01T12:00:00",
  "status": "pending",
  "executed_at": null,
  "execution_time_ms": null,
  "error_message": null,
  "dependencies": []
}
```

## 🔧 Configuration

### MigrationConfig Options

```python
config = MigrationConfig(
    migrations_dir="migrations",           # Directory for migration files
    auto_generate=True,                   # Auto-generate migrations
    validate_before_run=True,             # Validate before execution
    use_transactions=True,                # Use transactions for safety
    backup_before_migration=False,        # Create backups before migration
    max_rollback_depth=10,                # Maximum rollback depth
    allowed_dangerous_operations=[]       # Allowed dangerous operations
)
```

## 🛡️ Safety Features

### Migration Validation

The system validates migrations for:
- SQL syntax errors
- Missing semicolons
- Empty migration content
- Invalid file format

### Safety Checks

The system checks for dangerous operations:
- `DROP TABLE` statements
- `DROP DATABASE` statements
- `TRUNCATE` statements
- `DELETE FROM` without WHERE clause
- Data loss operations

### Rollback Protection

- Maximum rollback depth limits
- Dependency validation
- Transaction rollback on errors
- Backup creation (optional)

## 🔄 Migration Types

### Supported Operations

1. **Table Operations**
   - Create table
   - Drop table
   - Rename table

2. **Column Operations**
   - Add column
   - Drop column
   - Modify column
   - Rename column

3. **Index Operations**
   - Create index
   - Drop index

4. **Constraint Operations**
   - Add constraint
   - Drop constraint

5. **Data Operations**
   - Data migration
   - Custom SQL

## 📊 Database Support

### Supported Databases

- **PostgreSQL**: Full support with PostgreSQL-specific features
- **MySQL**: Full support with MySQL-specific features
- **SQLite**: Full support with SQLite-specific features

### Database-Specific Features

- **PostgreSQL**: JSONB fields, array types, custom functions
- **MySQL**: JSON fields, spatial types, custom functions
- **SQLite**: JSON1 extension, custom functions

## 🧪 Testing

### Running Tests

```bash
# Run migration system tests
python test_enhanced_migrations.py

# Test specific features
python -c "
import asyncio
from test_enhanced_migrations import test_migration_generation
asyncio.run(test_migration_generation())
"
```

### Test Coverage

The test suite covers:
- Migration generation
- Migration execution
- Rollback operations
- Schema management
- Multi-database support
- Validation and safety checks
- Complex migration scenarios

## 🚨 Error Handling

### Common Errors

1. **Dependency Conflicts**
   ```
   Error: Circular dependency detected involving migration_001
   Solution: Reorder migrations or split circular dependencies
   ```

2. **Validation Errors**
   ```
   Error: Migration validation failed: SQL syntax error
   Solution: Fix SQL syntax in migration file
   ```

3. **Safety Warnings**
   ```
   Warning: Dangerous operation detected: DROP TABLE
   Solution: Review migration or add to allowed operations
   ```

### Error Recovery

- **Transaction Rollback**: Automatic rollback on errors
- **Migration Status Tracking**: Track failed migrations
- **Error Logging**: Detailed error messages and stack traces
- **Recovery Procedures**: Manual recovery options

## 📈 Performance

### Optimization Features

- **Connection Pooling**: Efficient database connection management
- **Batch Operations**: Execute multiple migrations efficiently
- **Parallel Execution**: Execute independent migrations in parallel
- **Caching**: Cache schema information for faster operations

### Performance Tips

1. **Use Transactions**: Enable transactions for safety and performance
2. **Batch Migrations**: Group related changes in single migrations
3. **Optimize Dependencies**: Minimize migration dependencies
4. **Use Dry-Run**: Preview migrations before execution

## 🔮 Future Enhancements

### Planned Features

- **Migration Templates**: Pre-built templates for common operations
- **Migration Testing**: Automated testing of migrations
- **Migration Analytics**: Performance and usage analytics
- **Migration Scheduling**: Scheduled migration execution
- **Migration Rollback UI**: Web interface for migration management

### Contributing

To contribute to the migration system:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📚 Examples

### Complete Example

```python
import asyncio
from oxen.migrations.enhanced_engine import EnhancedMigrationEngine, MigrationConfig
from oxen.multi_db_engine import MultiDbEngine

async def main():
    # Setup
    engine = MultiDbEngine("postgresql://user:pass@localhost/db")
    await engine.connect()
    
    config = MigrationConfig(
        migrations_dir="migrations",
        validate_before_run=True,
        use_transactions=True
    )
    
    migration_engine = EnhancedMigrationEngine(engine, config)
    
    # Generate and execute migration
    migration = await migration_engine.makemigrations(
        models=[User, Category, Post],
        description="Add blog models",
        author="developer"
    )
    
    result = await migration_engine.migrate()
    print(f"Successfully executed {len(result.migrations_executed)} migrations")
    
    await engine.disconnect()

asyncio.run(main())
```

This enhanced migration system provides a robust, safe, and feature-rich solution for managing database schema changes in OxenORM applications. 