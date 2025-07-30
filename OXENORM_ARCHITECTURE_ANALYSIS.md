# OxenORM Architecture Analysis

## Overview

OxenORM is a high-performance Python ORM with a Rust backend, designed to provide the best of both worlds: Python's ease of use and Rust's performance. The architecture follows a hybrid approach where Python handles the ORM layer and Rust handles the database operations.

## Architecture Components

### 1. **Python Layer (ORM Interface)**

#### Core Modules:

**`oxen/__init__.py`** - Main entry point
- Exports all public APIs
- Handles Rust backend availability check
- Provides unified interface for models, fields, and operations

**`oxen/models.py`** - Model System (606 lines)
- **ModelMeta**: Metaclass for model creation and field registration
- **Model**: Base class for all ORM models
- **MetaInfo**: Dataclass for model metadata
- **Key Features**:
  - Field registration and validation
  - Primary key management
  - Signal handling (pre_save, post_save, pre_delete, post_delete)
  - Database operation methods (create, save, delete)
  - QuerySet generation

**`oxen/fields/`** - Field System
- **`base.py`**: Abstract base class for all fields
- **`data.py`**: Concrete field implementations (CharField, IntField, etc.)
- **`relational.py`**: Relationship fields (ForeignKey, ManyToMany, etc.)

**`oxen/queryset.py`** - Query System (722 lines)
- **QuerySet**: Main query builder class
- **QuerySetSingle**: Single result queries
- **AwaitableQuery**: Base for async queries
- **Key Features**:
  - Filter operations
  - Ordering and limiting
  - Aggregations (count, exists)
  - Bulk operations
  - Raw SQL support

**`oxen/engine.py`** - Database Engine (652 lines)
- **UnifiedEngine**: Main database interface
- **QueryCache**: LRU cache for query results
- **PerformanceMonitor**: Query performance tracking
- **UnifiedTransaction**: Transaction management

### 2. **Rust Layer (High-Performance Backend)**

#### Core Components:

**`src/lib.rs`** - Rust Backend (1016 lines)
- **OxenEngine**: Main Rust engine class
- **DatabasePool**: Connection pooling for different databases
- **OxenTransaction**: Transaction handling
- **Supported Databases**:
  - PostgreSQL (via sqlx)
  - MySQL (via sqlx)
  - SQLite (via sqlx)

**Key Rust Features**:
- **Connection Pooling**: Efficient database connection management
- **Async Operations**: Full async/await support
- **Type Safety**: Compile-time type checking
- **Memory Safety**: Rust's ownership system
- **Performance**: Zero-cost abstractions

### 3. **Bridge Layer**

**`oxen/rust_bridge.py`** - Python-Rust Bridge (157 lines)
- **OxenEngine**: Python wrapper around Rust engine
- **RUST_AVAILABLE**: Feature flag for Rust backend
- **Methods**:
  - `connect()`: Database connection
  - `insert_model()`: Insert operations
  - `update_model()`: Update operations
  - `delete_model()`: Delete operations
  - `query_models()`: Query operations
  - `bulk_insert()`: Bulk operations

## Working Process

### 1. **Initialization Process**

```python
# 1. Import and setup
from oxen import Model, CharField, connect

# 2. Define models
class User(Model):
    name = CharField(max_length=100)
    
# 3. Connect to database
await connect("sqlite:///test.db")
```

**Internal Process**:
1. **Model Registration**: `ModelMeta` processes class attributes
2. **Field Analysis**: Fields are categorized and validated
3. **Database Connection**: Rust engine establishes connection
4. **Table Creation**: Schema is generated and tables created

### 2. **Model Definition Process**

```python
class User(Model):
    name = CharField(max_length=100)
    age = IntField(default=0)
    
    class Meta:
        table_name = "users"
```

**Internal Process**:
1. **Metaclass Processing**: `ModelMeta.__new__()` processes class
2. **Field Registration**: Each field is registered in `MetaInfo`
3. **Validation Setup**: Field validators are configured
4. **Database Mapping**: Field-to-column mapping is established

### 3. **Create Operation Process**

```python
user = await User.create(name="John", age=30)
```

**Internal Process**:
1. **Validation**: Field values are validated
2. **Signal Dispatch**: `pre_save` signals are sent
3. **Rust Call**: Python calls Rust `insert_model()`
4. **Database Insert**: Rust executes SQL INSERT
5. **Signal Dispatch**: `post_save` signals are sent
6. **Instance Return**: Model instance is returned

### 4. **Query Operation Process**

```python
users = await User.filter(age__gte=18).all()
```

**Internal Process**:
1. **Query Building**: QuerySet constructs SQL
2. **Filter Resolution**: Filters are converted to WHERE clauses
3. **Rust Call**: Python calls Rust `query_models()`
4. **Database Query**: Rust executes SQL SELECT
5. **Result Processing**: Results are converted to model instances
6. **Instance Return**: List of model instances returned

## Database Support

### **Supported Databases**:

1. **SQLite** ✅ (Fully implemented)
   - File-based database
   - No server required
   - Good for development and small applications

2. **PostgreSQL** ✅ (Fully implemented)
   - Enterprise-grade database
   - Advanced features (JSON, arrays, etc.)
   - High performance and reliability

3. **MySQL** ✅ (Fully implemented)
   - Popular open-source database
   - Good performance
   - Wide community support

### **Connection String Format**:
```python
# SQLite
"sqlite:///path/to/database.db"

# PostgreSQL
"postgresql://user:password@host:port/database"

# MySQL
"mysql://user:password@host:port/database"
```

## Field System

### **Basic Fields** (Implemented):
- `CharField`: String with max length
- `TextField`: Unlimited text
- `IntField`: 32-bit integer
- `BooleanField`: True/false values
- `DateTimeField`: Date and time
- `DateField`: Date only
- `TimeField`: Time only

### **Advanced Fields** (Abstract - Not Implemented):
- `UUIDField`: UUID values
- `DecimalField`: Decimal numbers
- `JSONField`: JSON data
- `FileField`: File uploads
- `ImageField`: Image processing

### **Relational Fields** (Abstract - Not Implemented):
- `ForeignKeyField`: One-to-many relationships
- `OneToOneField`: One-to-one relationships
- `ManyToManyField`: Many-to-many relationships

## Query System

### **QuerySet Methods**:
```python
# Filtering
User.filter(age__gte=18)
User.exclude(is_active=False)

# Ordering
User.order_by("name", "-created_at")

# Limiting
User.limit(10).offset(20)

# Aggregations
User.count()
User.exists()

# Bulk operations
User.bulk_create([user1, user2, user3])
```

### **Query Building Process**:
1. **Filter Resolution**: Convert Python filters to SQL WHERE
2. **Join Generation**: Handle related field queries
3. **Order Resolution**: Convert ordering to SQL ORDER BY
4. **Limit/Offset**: Apply pagination
5. **SQL Generation**: Build final SQL query
6. **Parameter Binding**: Safely bind parameters

## Performance Features

### **Rust Backend Benefits**:
1. **Zero-Cost Abstractions**: No runtime overhead
2. **Memory Safety**: No memory leaks or buffer overflows
3. **Concurrent Safety**: Thread-safe operations
4. **Native Performance**: Direct database access

### **Caching System**:
1. **Query Cache**: LRU cache for query results
2. **Prepared Statements**: Reuse compiled queries
3. **Connection Pooling**: Efficient connection management

### **Performance Monitoring**:
1. **Query Metrics**: Track execution time
2. **Slow Query Detection**: Identify performance bottlenecks
3. **Statistics Collection**: Monitor usage patterns

## Signal System

### **Available Signals**:
```python
from oxen.signals import Signals

# Pre-save signal
@pre_save(User)
async def user_pre_save(sender, instance, **kwargs):
    print(f"About to save: {instance}")

# Post-save signal
@post_save(User)
async def user_post_save(sender, instance, created, **kwargs):
    if created:
        print(f"Created: {instance}")
    else:
        print(f"Updated: {instance}")
```

### **Signal Flow**:
1. **Registration**: Signals are registered during model definition
2. **Dispatch**: Signals are sent during model operations
3. **Async Support**: Signals can be async functions
4. **Error Handling**: Signal errors don't stop operations

## Error Handling

### **Exception Hierarchy**:
```python
OxenError (Base)
├── ConfigurationError
├── ConnectionError
├── ValidationError
├── IntegrityError
├── DoesNotExist
├── MultipleObjectsReturned
├── OperationalError
└── TransactionError
```

### **Error Handling Process**:
1. **Validation**: Field-level validation errors
2. **Database**: Database constraint violations
3. **Connection**: Network and connection issues
4. **Transaction**: Rollback on transaction errors

## Current Status (v0.1.0)

### **✅ Implemented Features**:
1. **Basic Model System**: Model definition and registration
2. **Basic Fields**: CharField, IntField, BooleanField, TextField
3. **Database Connection**: SQLite, PostgreSQL, MySQL support
4. **Create Operations**: Model creation works
5. **Rust Backend**: High-performance database operations
6. **Signal System**: Pre/post save/delete signals
7. **Query Building**: Basic query construction
8. **Connection Pooling**: Efficient connection management

### **❌ Missing Features**:
1. **Read Operations**: `Model.all()`, `Model.get()` return empty
2. **Update Operations**: `Model.update()` method not implemented
3. **Delete Operations**: `Model.delete()` method not implemented
4. **Advanced Fields**: UUIDField, DecimalField, JSONField are abstract
5. **Relational Fields**: ForeignKey, ManyToMany are abstract
6. **Query Execution**: QuerySet execution is not fully implemented
7. **Migrations**: Database schema migration system
8. **Transactions**: Full transaction support

## Development Roadmap

### **Phase 1: Core Operations** (Current)
- ✅ Model definition
- ✅ Basic fields
- ✅ Create operations
- ❌ Read operations (in progress)
- ❌ Update operations
- ❌ Delete operations

### **Phase 2: Advanced Features**
- ❌ Relational fields
- ❌ Advanced field types
- ❌ Query optimization
- ❌ Migration system

### **Phase 3: Production Features**
- ❌ Full transaction support
- ❌ Connection pooling optimization
- ❌ Performance monitoring
- ❌ Documentation and examples

## Conclusion

OxenORM represents an ambitious attempt to create a high-performance Python ORM by leveraging Rust's performance characteristics. The architecture is well-designed with clear separation between Python (ORM interface) and Rust (database operations).

**Strengths**:
- Clean architecture with clear separation of concerns
- High-performance Rust backend
- Comprehensive field system design
- Signal system for extensibility
- Support for multiple databases

**Current Limitations**:
- Many features are still abstract/unimplemented
- Query execution is incomplete
- Limited documentation and examples
- Early development stage (v0.1.0)

The project shows great promise but needs significant development to reach production readiness. The foundation is solid, but many core ORM features need to be implemented. 