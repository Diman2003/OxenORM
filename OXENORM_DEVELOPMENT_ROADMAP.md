# OxenORM Development Roadmap

## 🎯 Overview

This roadmap identifies all features that need improvement in OxenORM v0.1.0 and provides a prioritized development plan to bring the ORM to production readiness.

## 📊 Current Status Analysis

### **✅ Working Features**
- Model definition and registration
- Basic fields (CharField, IntField, BooleanField, TextField)
- Create operations (`Model.create()`)
- Database connections (SQLite, PostgreSQL, MySQL)
- Signal system (pre_save, post_save, pre_delete, post_delete)
- Query building (filters, ordering, limiting)
- Rust backend integration

### **❌ Critical Missing Features**
- Read operations (return empty results)
- Update operations (not implemented)
- Delete operations (not implemented)
- Query execution (incomplete)
- Advanced fields (abstract)
- Relational fields (abstract)
- Transaction support (incomplete)

## 🚀 Development Priorities

### **Phase 1: Core CRUD Operations** (HIGH PRIORITY)

#### **1.1 Read Operations Implementation**
**Files to modify:**
- `oxen/models.py` - Model read methods
- `oxen/queryset.py` - QuerySet execution
- `oxen/rust_bridge.py` - Rust query methods

**Tasks:**
```python
# 1. Implement Model.all() method
async def all(cls, using_db: Optional[Any] = None) -> List[Model]:
    """Get all model instances."""
    queryset = cls._db_queryset(using_db)
    return await queryset._execute()

# 2. Implement Model.get() method  
async def get(cls, *args: Q, using_db: Optional[Any] = None, **kwargs: Any) -> Model:
    """Get a single model instance."""
    queryset = cls.filter(*args, **kwargs)
    result = await queryset._execute()
    if not result:
        raise DoesNotExist(f"{cls.__name__} matching query does not exist")
    if len(result) > 1:
        raise MultipleObjectsReturned(f"Multiple {cls.__name__} objects returned")
    return result[0]

# 3. Implement QuerySet._execute() method
async def _execute(self) -> List[Model]:
    """Execute the query and return results."""
    # Build SQL query
    sql = self._make_query()
    
    # Execute via Rust backend
    result = await self._db.execute_query(sql, self._params)
    
    # Convert to model instances
    return [self.model._init_from_db(**row) for row in result]
```

#### **1.2 Update Operations Implementation**
**Files to modify:**
- `oxen/models.py` - Model update methods
- `oxen/queryset.py` - UpdateQuery class

**Tasks:**
```python
# 1. Implement Model.update() method
async def update(self, **kwargs: Any) -> None:
    """Update model instance."""
    if not self.pk:
        raise IntegrityError("Cannot update model without primary key")
    
    # Validate and set fields
    for key, value in kwargs.items():
        if key in self._meta.fields_map:
            field = self._meta.fields_map[key]
            setattr(self, key, field.to_python_value(value))
    
    # Execute update via Rust backend
    await self._db.update_model(
        self._meta.table_name,
        self.pk,
        {k: v for k, v in kwargs.items() if k in self._meta.fields_map}
    )

# 2. Implement QuerySet.update() method
async def update(self, **kwargs: Any) -> int:
    """Update all objects in queryset."""
    sql = self._make_update_query(kwargs)
    result = await self._db.execute_query(sql, self._params)
    return result.rows_affected
```

#### **1.3 Delete Operations Implementation**
**Files to modify:**
- `oxen/models.py` - Model delete methods
- `oxen/queryset.py` - DeleteQuery class

**Tasks:**
```python
# 1. Implement Model.delete() method
async def delete(self, using_db: Optional[Any] = None) -> None:
    """Delete model instance."""
    if not self.pk:
        raise IntegrityError("Cannot delete model without primary key")
    
    # Pre-delete hook
    await self._pre_delete(using_db)
    
    # Execute delete via Rust backend
    await self._db.delete_model(self._meta.table_name, self.pk)
    
    # Post-delete hook
    await self._post_delete(using_db)
    
    self._saved_in_db = False

# 2. Implement QuerySet.delete() method
async def delete(self) -> int:
    """Delete all objects in queryset."""
    sql = self._make_delete_query()
    result = await self._db.execute_query(sql, self._params)
    return result.rows_affected
```

### **Phase 2: Advanced Fields Implementation** (HIGH PRIORITY)

#### **2.1 UUIDField Implementation**
**File to modify:** `oxen/fields/data.py`

**Tasks:**
```python
class UUIDField(Field):
    """UUID field implementation."""
    
    def __init__(self, auto_generate: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.auto_generate = auto_generate
    
    def _validate(self, value: Any) -> Any:
        if isinstance(value, str):
            return uuid.UUID(value)
        elif isinstance(value, uuid.UUID):
            return value
        else:
            raise ValidationError(f"UUIDField must be a UUID or string, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return str(value)
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return uuid.UUID(value)
    
    def _get_sql_type(self) -> str:
        return "UUID"
```

#### **2.2 DecimalField Implementation**
**File to modify:** `oxen/fields/data.py`

**Tasks:**
```python
class DecimalField(Field):
    """Decimal field implementation."""
    
    def __init__(self, max_digits: Optional[int] = None, decimal_places: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places
    
    def _validate(self, value: Any) -> Any:
        if isinstance(value, (int, float, str)):
            decimal_value = Decimal(str(value))
        elif isinstance(value, Decimal):
            decimal_value = value
        else:
            raise ValidationError(f"DecimalField must be a number, got {type(value)}")
        
        # Validate precision
        if self.max_digits:
            digits = len(str(decimal_value).replace('.', '').replace('-', ''))
            if digits > self.max_digits:
                raise ValidationError(f"Decimal value exceeds max_digits of {self.max_digits}")
        
        return decimal_value
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return str(value)
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return Decimal(str(value))
    
    def _get_sql_type(self) -> str:
        if self.max_digits and self.decimal_places:
            return f"DECIMAL({self.max_digits},{self.decimal_places})"
        return "DECIMAL"
```

#### **2.3 JSONField Implementation**
**File to modify:** `oxen/fields/data.py`

**Tasks:**
```python
class JSONField(Field):
    """JSON field implementation."""
    
    def _validate(self, value: Any) -> Any:
        if value is None:
            return None
        
        # Ensure value is JSON serializable
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            raise ValidationError(f"JSONField value must be JSON serializable, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return json.dumps(value)
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value
    
    def _get_sql_type(self) -> str:
        return "JSON"
```

### **Phase 3: Relational Fields Implementation** (MEDIUM PRIORITY)

#### **3.1 ForeignKeyField Implementation**
**File to modify:** `oxen/fields/relational.py`

**Tasks:**
```python
class ForeignKeyField(RelationalField):
    """Foreign key field implementation."""
    
    def __init__(
        self,
        model: Union[str, Type[Any]],
        related_name: Optional[str] = None,
        on_delete: str = "CASCADE",
        on_update: str = "CASCADE",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.model = model
        self.related_name = related_name
        self.on_delete = on_delete
        self.on_update = on_update
    
    def _validate_value(self, value: Any) -> Any:
        if value is None:
            return None
        
        if isinstance(value, (int, str)):
            return value
        elif hasattr(value, 'pk'):
            return value.pk
        else:
            raise ValueError("Value must be an ID or model instance")
    
    def _get_sql_type(self) -> str:
        return "BIGINT"
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if hasattr(value, 'pk'):
            return value.pk
        return value
    
    def from_db_value(self, value: Any) -> Any:
        return value
```

#### **3.2 ManyToManyField Implementation**
**File to modify:** `oxen/fields/relational.py`

**Tasks:**
```python
class ManyToManyField(RelationalField):
    """Many-to-many field implementation."""
    
    def __init__(
        self,
        model: Union[str, Type[Any]],
        through: Optional[Union[str, Type[Any]]] = None,
        related_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.model = model
        self.through = through
        self.related_name = related_name
    
    def _validate_value(self, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        else:
            raise ValueError("Value must be a list or tuple")
    
    def _get_sql_type(self) -> str:
        raise NotImplementedError("ManyToManyField does not have a direct SQL type")
    
    def to_db_value(self, value: Any) -> Any:
        # ManyToMany fields are handled through junction tables
        return value
    
    def from_db_value(self, value: Any) -> Any:
        return value
```

### **Phase 4: Query System Enhancement** (MEDIUM PRIORITY)

#### **4.1 QuerySet Execution Implementation**
**File to modify:** `oxen/queryset.py`

**Tasks:**
```python
# 1. Implement QuerySetSingle.__await__()
def __await__(self) -> Generator[Any, None, T_co]:
    """Make the queryset awaitable."""
    async def _self() -> T_co:
        results = await self.queryset._execute()
        if not results:
            raise DoesNotExist(f"No {self.queryset.model.__name__} found")
        if len(results) > 1:
            raise MultipleObjectsReturned(f"Multiple {self.queryset.model.__name__} objects returned")
        return results[0]
    return _self().__await__()

# 2. Implement QuerySet._execute() with actual database calls
async def _execute(self) -> List[Model]:
    """Execute the query and return results."""
    # Build SQL query
    sql = self._make_query()
    
    # Execute via Rust backend
    result = await self._db.execute_query(sql, self._params)
    
    # Convert to model instances
    return [self.model._init_from_db(**row) for row in result]

# 3. Implement SQL generation methods
def _make_query(self) -> str:
    """Build the SQL query."""
    # Implement SQL generation logic
    pass

def _make_update_query(self, updates: Dict[str, Any]) -> str:
    """Build UPDATE SQL query."""
    # Implement UPDATE SQL generation
    pass

def _make_delete_query(self) -> str:
    """Build DELETE SQL query."""
    # Implement DELETE SQL generation
    pass
```

#### **4.2 Filter Resolution Implementation**
**File to modify:** `oxen/queryset.py`

**Tasks:**
```python
def resolve_filters(self) -> None:
    """Resolve filters to SQL WHERE clause."""
    where_conditions = []
    
    # Process custom filters
    for field, filter_info in self._custom_filters.items():
        condition = self._build_filter_condition(field, filter_info)
        where_conditions.append(condition)
    
    # Process Q objects
    for q_obj in self._q_objects:
        condition = self._resolve_q_object(q_obj)
        where_conditions.append(condition)
    
    if where_conditions:
        self.query += " WHERE " + " AND ".join(where_conditions)

def _build_filter_condition(self, field: str, filter_info: FilterInfoDict) -> str:
    """Build SQL condition from filter info."""
    # Implement filter condition building
    pass

def _resolve_q_object(self, q_obj: Q) -> str:
    """Resolve Q object to SQL condition."""
    # Implement Q object resolution
    pass
```

### **Phase 5: Transaction Support** (MEDIUM PRIORITY)

#### **5.1 Transaction Implementation**
**Files to modify:**
- `oxen/rust_bridge.py` - Transaction methods
- `oxen/engine.py` - Transaction context managers

**Tasks:**
```python
# 1. Implement OxenTransaction methods
class OxenTransaction:
    async def commit(self) -> None:
        """Commit the transaction"""
        if RUST_AVAILABLE:
            await self._rust_transaction.commit()
    
    async def rollback(self) -> None:
        """Rollback the transaction"""
        if RUST_AVAILABLE:
            await self._rust_transaction.rollback()

# 2. Implement transaction context managers
@asynccontextmanager
async def transaction(self):
    """Transaction context manager."""
    transaction = await self.begin_transaction()
    try:
        yield transaction
        await transaction.commit()
    except Exception:
        await transaction.rollback()
        raise
```

### **Phase 6: Migration System** (LOW PRIORITY)

#### **6.1 Migration Engine Implementation**
**Files to modify:**
- `oxen/migrations/engine.py`
- `oxen/migrations/generator.py`

**Tasks:**
```python
# 1. Implement migration generation
class MigrationGenerator:
    def generate_migration(self, changes: List[Change]) -> str:
        """Generate migration SQL from model changes."""
        up_sql = []
        down_sql = []
        
        for change in changes:
            if change.change_type == ChangeType.CREATE_TABLE:
                up_sql.append(self._generate_create_table_sql(change))
                down_sql.append(self._generate_drop_table_sql(change))
            elif change.change_type == ChangeType.ADD_COLUMN:
                up_sql.append(self._generate_add_column_sql(change))
                down_sql.append(self._generate_drop_column_sql(change))
        
        return "\n".join(up_sql), "\n".join(down_sql)

# 2. Implement migration execution
class MigrationEngine:
    async def apply_migration(self, migration: Migration) -> None:
        """Apply a migration."""
        await self._db.execute_query(migration.up_sql)
        await self._record_migration(migration)
    
    async def rollback_migration(self, migration: Migration) -> None:
        """Rollback a migration."""
        await self._db.execute_query(migration.down_sql)
        await self._remove_migration_record(migration)
```

### **Phase 7: Performance Optimizations** (LOW PRIORITY)

#### **7.1 Connection Pooling Enhancement**
**File to modify:** `oxen/engine.py`

**Tasks:**
```python
# 1. Implement connection pool monitoring
class ConnectionPool:
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            'total_connections': self.total_connections,
            'active_connections': self.active_connections,
            'idle_connections': self.idle_connections,
            'max_connections': self.max_connections,
            'connection_timeout': self.connection_timeout
        }

# 2. Implement query caching
class QueryCache:
    def get(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Get cached query result."""
        key = self._generate_key(sql, params)
        return self.cache.get(key)
    
    def set(self, sql: str, data: Any, params: Optional[Dict[str, Any]] = None, 
            ttl: Optional[int] = None) -> None:
        """Cache query result."""
        key = self._generate_key(sql, params)
        self.cache[key] = CacheEntry(data, datetime.now(), ttl or self.default_ttl)
```

#### **7.2 Query Optimization**
**File to modify:** `oxen/queryset.py`

**Tasks:**
```python
# 1. Implement query optimization
class QueryOptimizer:
    def optimize_query(self, queryset: QuerySet) -> QuerySet:
        """Optimize query for better performance."""
        # Implement query optimization logic
        return queryset
    
    def add_index_hints(self, queryset: QuerySet) -> QuerySet:
        """Add index hints to query."""
        # Implement index hint logic
        return queryset

# 2. Implement query analysis
class QueryAnalyzer:
    async def explain_query(self, queryset: QuerySet) -> Dict[str, Any]:
        """Explain query execution plan."""
        sql = queryset.sql()
        explain_sql = f"EXPLAIN {sql}"
        result = await queryset._db.execute_query(explain_sql)
        return result
```

## 📋 Implementation Checklist

### **Phase 1: Core CRUD Operations**
- [ ] **Read Operations**
  - [ ] Implement `Model.all()` method
  - [ ] Implement `Model.get()` method
  - [ ] Implement `Model.get_or_none()` method
  - [ ] Implement `QuerySet._execute()` method
  - [ ] Add SQL generation for SELECT queries
  - [ ] Add result conversion to model instances

- [ ] **Update Operations**
  - [ ] Implement `Model.update()` method
  - [ ] Implement `QuerySet.update()` method
  - [ ] Add SQL generation for UPDATE queries
  - [ ] Add field validation for updates

- [ ] **Delete Operations**
  - [ ] Implement `Model.delete()` method
  - [ ] Implement `QuerySet.delete()` method
  - [ ] Add SQL generation for DELETE queries
  - [ ] Add cascade delete support

### **Phase 2: Advanced Fields**
- [ ] **UUIDField**
  - [ ] Implement validation logic
  - [ ] Implement database conversion
  - [ ] Add auto-generation support
  - [ ] Add SQL type mapping

- [ ] **DecimalField**
  - [ ] Implement precision validation
  - [ ] Implement database conversion
  - [ ] Add max_digits/decimal_places support
  - [ ] Add SQL type mapping

- [ ] **JSONField**
  - [ ] Implement JSON serialization
  - [ ] Implement database conversion
  - [ ] Add JSON validation
  - [ ] Add SQL type mapping

### **Phase 3: Relational Fields**
- [ ] **ForeignKeyField**
  - [ ] Implement relationship validation
  - [ ] Implement database conversion
  - [ ] Add on_delete/on_update support
  - [ ] Add related_name support

- [ ] **ManyToManyField**
  - [ ] Implement junction table creation
  - [ ] Implement relationship management
  - [ ] Add through model support
  - [ ] Add add/remove/clear methods

### **Phase 4: Query System**
- [ ] **QuerySet Execution**
  - [ ] Implement SQL generation
  - [ ] Implement parameter binding
  - [ ] Add result conversion
  - [ ] Add error handling

- [ ] **Filter Resolution**
  - [ ] Implement filter condition building
  - [ ] Implement Q object resolution
  - [ ] Add complex filter support
  - [ ] Add join generation

### **Phase 5: Transactions**
- [ ] **Transaction Support**
  - [ ] Implement transaction begin/commit/rollback
  - [ ] Add transaction context managers
  - [ ] Add nested transaction support
  - [ ] Add transaction isolation levels

### **Phase 6: Migrations**
- [ ] **Migration System**
  - [ ] Implement migration generation
  - [ ] Implement migration execution
  - [ ] Add migration rollback
  - [ ] Add migration history tracking

### **Phase 7: Performance**
- [ ] **Connection Pooling**
  - [ ] Implement connection monitoring
  - [ ] Add connection health checks
  - [ ] Add connection pool statistics
  - [ ] Add connection timeout handling

- [ ] **Query Optimization**
  - [ ] Implement query caching
  - [ ] Add query analysis
  - [ ] Add index hints
  - [ ] Add query optimization

## 🎯 Success Metrics

### **Phase 1 Success Criteria**
- [ ] All CRUD operations work correctly
- [ ] Query results are properly converted to model instances
- [ ] Error handling is comprehensive
- [ ] Performance is acceptable for basic operations

### **Phase 2 Success Criteria**
- [ ] All advanced fields work correctly
- [ ] Field validation is comprehensive
- [ ] Database type mapping is correct
- [ ] Auto-generation works properly

### **Phase 3 Success Criteria**
- [ ] All relational fields work correctly
- [ ] Relationship queries work efficiently
- [ ] Cascade operations work properly
- [ ] Related object access works correctly

### **Overall Success Criteria**
- [ ] 100% test coverage for implemented features
- [ ] Performance benchmarks show improvement
- [ ] Documentation is complete and accurate
- [ ] API is stable and well-designed

## 🚀 Next Steps

1. **Start with Phase 1**: Implement core CRUD operations
2. **Create comprehensive tests**: For each implemented feature
3. **Update documentation**: As features are implemented
4. **Performance testing**: Ensure improvements are measurable
5. **Community feedback**: Gather input on API design

This roadmap provides a clear path to bring OxenORM from its current early development state to production readiness. Each phase builds upon the previous one, ensuring a solid foundation for the next set of features. 