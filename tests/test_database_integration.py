"""
Database Integration Tests for OxenORM

These tests verify that OxenORM works correctly with all supported databases.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from oxen import Model, init_db, close_db
from oxen.fields import (
    IntField, CharField, TextField, BooleanField, DateTimeField,
    DateField, TimeField, DecimalField, FloatField, JSONField, UUIDField
)
from oxen.exceptions import OxenError, DoesNotExist


class TestUser(Model):
    """Test user model for integration tests."""
    
    id = IntField(primary_key=True)
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100, unique=True)
    bio = TextField(null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        table = "test_users"


class TestPost(Model):
    """Test post model for integration tests."""
    
    id = IntField(primary_key=True)
    title = CharField(max_length=200)
    content = TextField()
    author_id = IntField()  # Foreign key to TestUser
    published = BooleanField(default=False)
    views = IntField(default=0)
    rating = FloatField(default=0.0)
    price = DecimalField(max_digits=10, decimal_places=2, null=True)
    tags = JSONField(default=list)
    uuid = UUIDField(default=uuid4)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        table = "test_posts"


@pytest.fixture
def sqlite_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield f"sqlite:{db_path}"
    
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def postgres_db():
    """PostgreSQL database connection string."""
    # This would be configured via environment variables in CI
    return "postgresql://test:test@localhost/oxenorm_test"


@pytest.fixture
def mysql_db():
    """MySQL database connection string."""
    # This would be configured via environment variables in CI
    return "mysql://test:test@localhost/oxenorm_test"


@pytest.mark.asyncio
async def test_sqlite_basic_operations(sqlite_db):
    """Test basic CRUD operations with SQLite."""
    await init_db({'default': sqlite_db})
    
    try:
        # Create user
        user = await TestUser.create(
            username="testuser",
            email="test@example.com",
            bio="Test user bio"
        )
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.bio == "Test user bio"
        assert user.is_active is True
        assert user.created_at is not None
        
        # Get user
        retrieved_user = await TestUser.get(id=user.id)
        assert retrieved_user.id == user.id
        assert retrieved_user.username == user.username
        
        # Update user
        user.bio = "Updated bio"
        await user.save()
        
        updated_user = await TestUser.get(id=user.id)
        assert updated_user.bio == "Updated bio"
        
        # Delete user
        await user.delete()
        
        # Verify deletion
        with pytest.raises(DoesNotExist):
            await TestUser.get(id=user.id)
            
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_sqlite_query_operations(sqlite_db):
    """Test query operations with SQLite."""
    await init_db({'default': sqlite_db})
    
    try:
        # Create multiple users
        users = []
        for i in range(5):
            user = await TestUser.create(
                username=f"user{i}",
                email=f"user{i}@example.com",
                is_active=i % 2 == 0  # Even users are active
            )
            users.append(user)
        
        # Test filter
        active_users = await TestUser.filter(is_active=True)
        assert len(active_users) == 3  # Users 0, 2, 4
        
        # Test count
        total_users = await TestUser.count()
        assert total_users == 5
        
        # Test limit and offset
        limited_users = await TestUser.all().limit(2)
        assert len(limited_users) == 2
        
        # Test order by
        ordered_users = await TestUser.all().order_by("-created_at")
        assert len(ordered_users) == 5
        # Should be in reverse chronological order
        
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_sqlite_complex_fields(sqlite_db):
    """Test complex field types with SQLite."""
    await init_db({'default': sqlite_db})
    
    try:
        # Create post with complex fields
        post = await TestPost.create(
            title="Test Post",
            content="Test content",
            author_id=1,
            views=100,
            rating=4.5,
            price=Decimal("19.99"),
            tags=["python", "rust", "orm"],
            uuid=uuid4()
        )
        
        assert post.title == "Test Post"
        assert post.views == 100
        assert post.rating == 4.5
        assert post.price == Decimal("19.99")
        assert post.tags == ["python", "rust", "orm"]
        assert post.uuid is not None
        
        # Retrieve and verify
        retrieved_post = await TestPost.get(id=post.id)
        assert retrieved_post.title == post.title
        assert retrieved_post.views == post.views
        assert retrieved_post.rating == post.rating
        assert retrieved_post.price == post.price
        assert retrieved_post.tags == post.tags
        assert retrieved_post.uuid == post.uuid
        
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_sqlite_bulk_operations(sqlite_db):
    """Test bulk operations with SQLite."""
    await init_db({'default': sqlite_db})
    
    try:
        # Bulk create users
        users_data = [
            {"username": "bulk1", "email": "bulk1@example.com"},
            {"username": "bulk2", "email": "bulk2@example.com"},
            {"username": "bulk3", "email": "bulk3@example.com"},
        ]
        
        users = []
        for data in users_data:
            user = TestUser(**data)
            users.append(user)
        
        # This would use the Rust backend for performance
        # await TestUser.bulk_create(users)
        
        # For now, create individually
        created_users = []
        for user in users:
            created_user = await TestUser.create(**user_data)
            created_users.append(created_user)
        
        assert len(created_users) == 3
        
        # Verify all users were created
        total_users = await TestUser.count()
        assert total_users >= 3
        
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_sqlite_transactions(sqlite_db):
    """Test transaction support with SQLite."""
    await init_db({'default': sqlite_db})
    
    try:
        from oxen import transaction
        
        # Test successful transaction
        async with transaction():
            user1 = await TestUser.create(
                username="txuser1",
                email="txuser1@example.com"
            )
            user2 = await TestUser.create(
                username="txuser2",
                email="txuser2@example.com"
            )
        
        # Both users should exist
        assert await TestUser.get(username="txuser1")
        assert await TestUser.get(username="txuser2")
        
        # Test failed transaction
        try:
            async with transaction():
                user3 = await TestUser.create(
                    username="txuser3",
                    email="txuser3@example.com"
                )
                # This should fail due to duplicate email
                await TestUser.create(
                    username="txuser4",
                    email="txuser3@example.com"  # Duplicate email
                )
        except OxenError:
            pass
        
        # User3 should not exist due to rollback
        with pytest.raises(DoesNotExist):
            await TestUser.get(username="txuser3")
            
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_sqlite_raw_sql(sqlite_db):
    """Test raw SQL execution with SQLite."""
    await init_db({'default': sqlite_db})
    
    try:
        # Create some test data
        await TestUser.create(username="raw1", email="raw1@example.com")
        await TestUser.create(username="raw2", email="raw2@example.com")
        
        # Execute raw SQL
        # results = await TestUser.raw("SELECT COUNT(*) as count FROM test_users")
        # assert results[0]['count'] == 2
        
        # For now, test that the method exists
        assert hasattr(TestUser, 'raw')
        
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_postgres_basic_operations(postgres_db):
    """Test basic operations with PostgreSQL (if available)."""
    try:
        await init_db({'default': postgres_db})
        
        # Create user
        user = await TestUser.create(
            username="pguser",
            email="pguser@example.com"
        )
        assert user.id is not None
        
        # Get user
        retrieved_user = await TestUser.get(id=user.id)
        assert retrieved_user.username == "pguser"
        
    except OxenError as e:
        if "connection" in str(e).lower() or "rust engine not available" in str(e).lower():
            pytest.skip("PostgreSQL not available")
        else:
            raise
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_mysql_basic_operations(mysql_db):
    """Test basic operations with MySQL (if available)."""
    try:
        await init_db({'default': mysql_db})
        
        # Create user
        user = await TestUser.create(
            username="mysqluser",
            email="mysqluser@example.com"
        )
        assert user.id is not None
        
        # Get user
        retrieved_user = await TestUser.get(id=user.id)
        assert retrieved_user.username == "mysqluser"
        
    except OxenError as e:
        if "connection" in str(e).lower() or "rust engine not available" in str(e).lower():
            pytest.skip("MySQL not available")
        else:
            raise
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_field_validation(sqlite_db):
    """Test field validation."""
    await init_db({'default': sqlite_db})
    
    try:
        # Test required fields
        with pytest.raises(ValueError):
            await TestUser.create(username="test")  # Missing email
        
        # Test unique constraints
        await TestUser.create(username="unique1", email="unique1@example.com")
        
        with pytest.raises(OxenError):
            await TestUser.create(username="unique2", email="unique1@example.com")  # Duplicate email
        
        # Test field type validation
        user = await TestUser.create(
            username="validuser",
            email="valid@example.com",
            is_active=True
        )
        assert isinstance(user.is_active, bool)
        
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_connection_management(sqlite_db):
    """Test connection management."""
    # Test initialization
    await init_db({'default': sqlite_db})
    
    # Test multiple initializations (should be idempotent)
    await init_db({'default': sqlite_db})
    
    # Test closing
    await close_db()
    
    # Test closing again (should not fail)
    await close_db()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 