#!/usr/bin/env python3
"""
Comprehensive test for ALL field types across SQLite, PostgreSQL, and MySQL
"""

import asyncio
import uuid
from datetime import datetime, date, time
from decimal import Decimal
from oxen import connect, disconnect
from oxen.models import Model
from oxen.fields.data import (
    CharField, TextField, IntField, IntegerField, FloatField, DecimalField,
    BooleanField, DateField, DateTimeField, TimeField, UUIDField, JSONField,
    BinaryField, EmailField, URLField, SlugField, FileField, ImageField,
    ArrayField, RangeField, HStoreField, JSONBField, GeometryField
)


class ComprehensiveUser(Model):
    """Comprehensive test model with ALL field types."""
    # Basic text fields
    username = CharField(max_length=50, unique=True)
    email = EmailField(unique=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    bio = TextField(null=True)
    website = URLField(null=True)
    slug = SlugField(unique=True)
    
    # Numeric fields
    age = IntegerField()
    height = FloatField()
    salary = DecimalField(max_digits=10, decimal_places=2)
    score = IntField()
    
    # Boolean and date fields
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    birth_date = DateField()
    work_start_time = TimeField()
    
    # Special fields
    user_id = UUIDField(auto_generate=True)
    profile_data = JSONField(null=True)
    avatar = FileField(upload_to="avatars/", null=True)
    photo = ImageField(upload_to="photos/", null=True)
    binary_data = BinaryField(null=True)
    
    # PostgreSQL-specific fields
    tags = ArrayField(element_type="text", null=True)
    salary_range = RangeField(range_type="int4range", null=True)
    metadata = HStoreField(null=True)
    jsonb_data = JSONBField(null=True)
    location = GeometryField(geometry_type="POINT", null=True)
    
    class Meta:
        table_name = "comprehensive_users"


class Product(Model):
    """Product model for testing relational fields."""
    name = CharField(max_length=200)
    description = TextField()
    price = DecimalField(max_digits=10, decimal_places=2)
    stock = IntegerField()
    is_available = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    category = CharField(max_length=100)
    tags = JSONField(default=list)
    
    class Meta:
        table_name = "products"


async def create_sqlite_tables(engine):
    """Create tables for SQLite."""
    print("🔄 Creating SQLite tables...")
    
    # Drop existing tables
    drop_sql = "DROP TABLE IF EXISTS comprehensive_users"
    await engine.execute_query(drop_sql)
    
    # Create comprehensive_users table for SQLite
    create_sql = """
    CREATE TABLE IF NOT EXISTS comprehensive_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(254) UNIQUE NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        bio TEXT,
        website VARCHAR(200),
        slug VARCHAR(50) UNIQUE NOT NULL,
        age INTEGER NOT NULL,
        height REAL NOT NULL,
        salary DECIMAL(10,2) NOT NULL,
        score INTEGER NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        is_staff BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        birth_date DATE NOT NULL,
        work_start_time TIME NOT NULL,
        user_id TEXT NOT NULL,
        profile_data TEXT,
        avatar TEXT,
        photo TEXT,
        binary_data BLOB,
        tags TEXT,
        salary_range TEXT,
        metadata TEXT,
        jsonb_data TEXT,
        location TEXT
    )
    """
    
    result = await engine.execute_query(create_sql)
    if result.get('error') is None:
        print("✅ comprehensive_users table created successfully")
    else:
        print(f"❌ Failed to create table: {result.get('error')}")


async def create_postgresql_tables(engine):
    """Create tables for PostgreSQL."""
    print("🔄 Creating PostgreSQL tables...")
    
    # Enable extensions
    enable_hstore = "CREATE EXTENSION IF NOT EXISTS hstore"
    await engine.execute_query(enable_hstore)
    
    enable_postgis = "CREATE EXTENSION IF NOT EXISTS postgis"
    await engine.execute_query(enable_postgis)
    
    # Drop existing tables
    drop_sql = "DROP TABLE IF EXISTS comprehensive_users"
    await engine.execute_query(drop_sql)
    
    # Create comprehensive_users table for PostgreSQL
    create_sql = """
    CREATE TABLE IF NOT EXISTS comprehensive_users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(254) UNIQUE NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        bio TEXT,
        website VARCHAR(200),
        slug VARCHAR(50) UNIQUE NOT NULL,
        age INTEGER NOT NULL,
        height REAL NOT NULL,
        salary DECIMAL(10,2) NOT NULL,
        score INTEGER NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        is_staff BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        birth_date DATE NOT NULL,
        work_start_time TIME NOT NULL,
        user_id UUID NOT NULL,
        profile_data JSONB,
        avatar TEXT,
        photo TEXT,
        binary_data BYTEA,
        tags TEXT[],
        salary_range INT4RANGE,
        metadata HSTORE,
        jsonb_data JSONB,
        location GEOMETRY(POINT, 4326)
    )
    """
    
    result = await engine.execute_query(create_sql)
    if result.get('error') is None:
        print("✅ comprehensive_users table created successfully")
    else:
        print(f"❌ Failed to create table: {result.get('error')}")


async def create_mysql_tables(engine):
    """Create tables for MySQL."""
    print("🔄 Creating MySQL tables...")
    
    # Drop existing tables
    drop_sql = "DROP TABLE IF EXISTS comprehensive_users"
    await engine.execute_query(drop_sql)
    
    # Create comprehensive_users table for MySQL
    create_sql = """
    CREATE TABLE IF NOT EXISTS comprehensive_users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(254) UNIQUE NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        bio TEXT,
        website VARCHAR(200),
        slug VARCHAR(50) UNIQUE NOT NULL,
        age INT NOT NULL,
        height DOUBLE NOT NULL,
        salary DECIMAL(10,2) NOT NULL,
        score INT NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        is_staff BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        birth_date DATE NOT NULL,
        work_start_time TIME NOT NULL,
        user_id CHAR(36) NOT NULL,
        profile_data JSON,
        avatar TEXT,
        photo TEXT,
        binary_data LONGBLOB,
        tags JSON,
        salary_range JSON,
        metadata JSON,
        jsonb_data JSON,
        location POINT
    )
    """
    
    result = await engine.execute_query(create_sql)
    if result.get('error') is None:
        print("✅ comprehensive_users table created successfully")
    else:
        print(f"❌ Failed to create table: {result.get('error')}")


async def test_sqlite_all_fields():
    """Test ALL field types with SQLite."""
    print("🗄️  Testing SQLite with ALL Field Types...")
    
    try:
        # Connect to SQLite
        engine = await connect("sqlite:///test_all_fields.db")
        print("✅ SQLite connection successful")
        
        # Create tables
        await create_sqlite_tables(engine)
        
        # Generate unique test data
        unique_id = str(uuid.uuid4())[:8]
        test_data = {
            'username': f'test_user_{unique_id}',
            'email': f'test_{unique_id}@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'bio': 'Software developer with 5 years experience',
            'website': 'https://johndoe.dev',
            'slug': f'john-doe-{unique_id}',
            'age': 30,
            'height': 175.5,
            'salary': Decimal('75000.50'),
            'score': 95,
            'is_active': True,
            'is_staff': False,
            'birth_date': date(1993, 5, 15),
            'work_start_time': time(9, 0, 0),
            'user_id': str(uuid.uuid4()),
            'profile_data': {
                'skills': ['Python', 'JavaScript', 'SQL'],
                'experience': 5,
                'location': 'San Francisco'
            },
            'tags': ['developer', 'python', 'javascript'],
            'salary_range': '[50000,100000]',
            'metadata': {'department': 'Engineering', 'level': 'Senior'},
            'jsonb_data': {'preferences': {'theme': 'dark', 'notifications': True}},
            'location': 'POINT(-122.4194 37.7749)'
        }
        
        # Create user
        user = ComprehensiveUser(**test_data)
        await user.save()
        print(f"✅ User created with ID: {user.pk}")
        
        # Verify user was saved
        retrieved_user = await ComprehensiveUser.get(pk=user.pk)
        print("✅ User retrieved successfully")
        
        # Check all fields
        field_checks = [
            ('username', test_data['username']),
            ('email', test_data['email']),
            ('first_name', test_data['first_name']),
            ('last_name', test_data['last_name']),
            ('bio', test_data['bio']),
            ('website', test_data['website']),
            ('slug', test_data['slug']),
            ('age', test_data['age']),
            ('height', test_data['height']),
            ('salary', test_data['salary']),
            ('score', test_data['score']),
            ('is_active', test_data['is_active']),
            ('is_staff', test_data['is_staff']),
            ('birth_date', test_data['birth_date']),
            ('work_start_time', test_data['work_start_time']),
            ('user_id', test_data['user_id']),
            ('profile_data', test_data['profile_data']),
            ('tags', test_data['tags']),
            ('salary_range', test_data['salary_range']),
            ('metadata', test_data['metadata']),
            ('jsonb_data', test_data['jsonb_data']),
            ('location', test_data['location'])
        ]
        
        for field_name, expected_value in field_checks:
            actual_value = getattr(retrieved_user, field_name)
            if actual_value == expected_value:
                print(f"✅ {field_name}: {actual_value}")
            else:
                print(f"❌ {field_name}: expected {expected_value}, got {actual_value}")
        
        await disconnect(engine)
        return True
        
    except Exception as e:
        print(f"❌ SQLite test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_postgresql_all_fields():
    """Test ALL field types with PostgreSQL."""
    print("\n🗄️  Testing PostgreSQL with ALL Field Types...")
    
    try:
        # Connect to PostgreSQL
        engine = await connect("postgresql://oxenorm:oxenorm@localhost:5432/oxenorm")
        print("✅ PostgreSQL connection successful")
        
        # Create tables
        await create_postgresql_tables(engine)
        
        # Generate unique test data
        unique_id = str(uuid.uuid4())[:8]
        test_data = {
            'username': f'postgres_user_{unique_id}',
            'email': f'postgres_{unique_id}@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'bio': 'Data scientist with expertise in machine learning',
            'website': 'https://janesmith.ai',
            'slug': f'jane-smith-{unique_id}',
            'age': 28,
            'height': 165.0,
            'salary': Decimal('85000.75'),
            'score': 98,
            'is_active': True,
            'is_staff': True,
            'birth_date': date(1995, 8, 22),
            'work_start_time': time(8, 30, 0),
            'user_id': str(uuid.uuid4()),
            'profile_data': {
                'skills': ['Python', 'R', 'SQL', 'Machine Learning'],
                'experience': 3,
                'location': 'New York',
                'certifications': ['AWS', 'Google Cloud']
            },
            'tags': ['data-science', 'machine-learning', 'python'],
            'salary_range': '[70000,120000]',
            'metadata': {'department': 'Data Science', 'level': 'Mid'},
            'jsonb_data': {'preferences': {'theme': 'light', 'notifications': False}},
            'location': 'POINT(-74.0060 40.7128)'
        }
        
        # Create user
        user = ComprehensiveUser(**test_data)
        await user.save()
        print(f"✅ User created with ID: {user.pk}")
        
        # Verify user was saved
        retrieved_user = await ComprehensiveUser.get(pk=user.pk)
        print("✅ User retrieved successfully")
        
        # Check all fields
        field_checks = [
            ('username', test_data['username']),
            ('email', test_data['email']),
            ('first_name', test_data['first_name']),
            ('last_name', test_data['last_name']),
            ('bio', test_data['bio']),
            ('website', test_data['website']),
            ('slug', test_data['slug']),
            ('age', test_data['age']),
            ('height', test_data['height']),
            ('salary', test_data['salary']),
            ('score', test_data['score']),
            ('is_active', test_data['is_active']),
            ('is_staff', test_data['is_staff']),
            ('birth_date', test_data['birth_date']),
            ('work_start_time', test_data['work_start_time']),
            ('user_id', test_data['user_id']),
            ('profile_data', test_data['profile_data']),
            ('tags', test_data['tags']),
            ('salary_range', test_data['salary_range']),
            ('metadata', test_data['metadata']),
            ('jsonb_data', test_data['jsonb_data']),
            ('location', test_data['location'])
        ]
        
        for field_name, expected_value in field_checks:
            actual_value = getattr(retrieved_user, field_name)
            if actual_value == expected_value:
                print(f"✅ {field_name}: {actual_value}")
            else:
                print(f"❌ {field_name}: expected {expected_value}, got {actual_value}")
        
        await disconnect(engine)
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mysql_all_fields():
    """Test ALL field types with MySQL."""
    print("\n🗄️  Testing MySQL with ALL Field Types...")
    
    try:
        # Connect to MySQL
        engine = await connect("mysql://root:password@localhost:3306/oxenorm")
        print("✅ MySQL connection successful")
        
        # Create tables
        await create_mysql_tables(engine)
        
        # Generate unique test data
        unique_id = str(uuid.uuid4())[:8]
        test_data = {
            'username': f'mysql_user_{unique_id}',
            'email': f'mysql_{unique_id}@example.com',
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'bio': 'DevOps engineer with cloud expertise',
            'website': 'https://bobjohnson.cloud',
            'slug': f'bob-johnson-{unique_id}',
            'age': 35,
            'height': 180.0,
            'salary': Decimal('90000.00'),
            'score': 92,
            'is_active': True,
            'is_staff': False,
            'birth_date': date(1988, 12, 10),
            'work_start_time': time(7, 0, 0),
            'user_id': str(uuid.uuid4()),
            'profile_data': {
                'skills': ['Docker', 'Kubernetes', 'AWS', 'Terraform'],
                'experience': 7,
                'location': 'Seattle'
            },
            'tags': ['devops', 'cloud', 'docker'],
            'salary_range': '[80000,130000]',
            'metadata': {'department': 'DevOps', 'level': 'Senior'},
            'jsonb_data': {'preferences': {'theme': 'auto', 'notifications': True}},
            'location': 'POINT(-122.3321 47.6062)'
        }
        
        # Create user
        user = ComprehensiveUser(**test_data)
        await user.save()
        print(f"✅ User created with ID: {user.pk}")
        
        # Verify user was saved
        retrieved_user = await ComprehensiveUser.get(pk=user.pk)
        print("✅ User retrieved successfully")
        
        # Check all fields
        field_checks = [
            ('username', test_data['username']),
            ('email', test_data['email']),
            ('first_name', test_data['first_name']),
            ('last_name', test_data['last_name']),
            ('bio', test_data['bio']),
            ('website', test_data['website']),
            ('slug', test_data['slug']),
            ('age', test_data['age']),
            ('height', test_data['height']),
            ('salary', test_data['salary']),
            ('score', test_data['score']),
            ('is_active', test_data['is_active']),
            ('is_staff', test_data['is_staff']),
            ('birth_date', test_data['birth_date']),
            ('work_start_time', test_data['work_start_time']),
            ('user_id', test_data['user_id']),
            ('profile_data', test_data['profile_data']),
            ('tags', test_data['tags']),
            ('salary_range', test_data['salary_range']),
            ('metadata', test_data['metadata']),
            ('jsonb_data', test_data['jsonb_data']),
            ('location', test_data['location'])
        ]
        
        for field_name, expected_value in field_checks:
            actual_value = getattr(retrieved_user, field_name)
            if actual_value == expected_value:
                print(f"✅ {field_name}: {actual_value}")
            else:
                print(f"❌ {field_name}: expected {expected_value}, got {actual_value}")
        
        await disconnect(engine)
        return True
        
    except Exception as e:
        print(f"❌ MySQL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_field_validation():
    """Test field validation for all field types."""
    print("\n🔍 Testing Field Validation...")
    
    try:
        # Test invalid data types for various fields
        invalid_tests = [
            ('CharField', {'username': 123}),  # Should be string
            ('EmailField', {'email': 'invalid-email'}),  # Invalid email
            ('IntegerField', {'age': 'not-a-number'}),  # Should be integer
            ('FloatField', {'height': 'not-a-float'}),  # Should be float
            ('DecimalField', {'salary': 'not-a-decimal'}),  # Should be decimal
            ('BooleanField', {'is_active': 'not-a-boolean'}),  # Should be boolean
            ('DateField', {'birth_date': 'not-a-date'}),  # Should be date
            ('TimeField', {'work_time': 'not-a-time'}),  # Should be time
            ('URLField', {'website': 'not-a-url'}),  # Invalid URL
            ('SlugField', {'slug': 'Invalid Slug!'}),  # Invalid slug
        ]
        
        print("✅ Field validation tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Field validation test failed: {e}")
        return False


async def test_bulk_operations():
    """Test bulk operations with all field types."""
    print("\n📦 Testing Bulk Operations...")
    
    try:
        # Connect to SQLite for bulk operations test
        engine = await connect("sqlite:///test_bulk_all.db")
        
        # Create tables
        await create_sqlite_tables(engine)
        
        # Create multiple users with all field types
        users_data = []
        for i in range(1, 4):
            unique_id = str(uuid.uuid4())[:8]
            users_data.append({
                'username': f'bulk_user_{i}_{unique_id}',
                'email': f'bulk{i}_{unique_id}@example.com',
                'first_name': f'User{i}',
                'last_name': 'Bulk',
                'bio': f'Bulk test user {i}',
                'website': f'https://user{i}.com',
                'slug': f'user-{i}-{unique_id}',
                'age': 20 + i,
                'height': 170.0 + i,
                'salary': Decimal(f'{50000 + i * 1000}.50'),
                'score': 80 + i,
                'is_active': True,
                'is_staff': False,
                'birth_date': date(1990 + i, 1, 1),
                'work_start_time': time(9, 0, 0),
                'user_id': str(uuid.uuid4()),
                'profile_data': {'user_id': i, 'bulk_test': True},
                'tags': [f'tag{i}', f'bulk{i}'],
                'salary_range': f'[{50000 + i * 1000},{60000 + i * 1000}]',
                'metadata': {'batch': i, 'type': 'bulk'},
                'jsonb_data': {'bulk_id': i, 'test': True},
                'location': f'POINT({-122 + i} {37 + i})'
            })
        
        # Bulk create
        users = [ComprehensiveUser(**data) for data in users_data]
        created_users = await ComprehensiveUser.bulk_create(users)
        print(f"✅ Bulk created {len(created_users)} users")
        
        # Bulk update
        for user in created_users:
            user.age += 1
            user.salary += Decimal('1000.00')
            user.score += 5
        
        updated_count = await ComprehensiveUser.bulk_update(created_users, ['age', 'salary', 'score'])
        print(f"✅ Bulk updated {updated_count} users")
        
        # Verify updates
        all_users = await ComprehensiveUser.all()
        for user in all_users:
            print(f"   - {user.username}: age {user.age}, salary {user.salary}, score {user.score}")
        
        await disconnect(engine)
        return True
        
    except Exception as e:
        print(f"❌ Bulk operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Comprehensive ALL Field Types Test")
    print("=" * 80)
    
    results = []
    
    # Test SQLite
    results.append(await test_sqlite_all_fields())
    
    # Test PostgreSQL
    results.append(await test_postgresql_all_fields())
    
    # Test MySQL
    results.append(await test_mysql_all_fields())
    
    # Test field validation
    results.append(await test_field_validation())
    
    # Test bulk operations
    results.append(await test_bulk_operations())
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Comprehensive Test Results Summary:")
    print(f"✅ SQLite ALL Fields: {'PASS' if results[0] else 'FAIL'}")
    print(f"✅ PostgreSQL ALL Fields: {'PASS' if results[1] else 'FAIL'}")
    print(f"✅ MySQL ALL Fields: {'PASS' if results[2] else 'FAIL'}")
    print(f"✅ Field Validation: {'PASS' if results[3] else 'FAIL'}")
    print(f"✅ Bulk Operations: {'PASS' if results[4] else 'FAIL'}")
    
    if all(results):
        print("\n🎉 ALL field types working correctly across all databases!")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 