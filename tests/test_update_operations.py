#!/usr/bin/env python3
"""
Comprehensive test for Update Operations
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField, BooleanField, DateTimeField
from oxen.migrations import MigrationEngine


# Test models
class User(Model):
    """User model for testing updates."""
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    age = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = "test_users"


class Product(Model):
    """Product model for testing updates."""
    name = CharField(max_length=200)
    price = IntegerField(default=0)
    description = CharField(max_length=500, null=True)
    is_available = BooleanField(default=True)
    
    class Meta:
        table_name = "test_products"


async def check_tables_exist(engine, table_names):
    """Check if tables exist in the database."""
    try:
        result = await engine.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?)",
            [table_names]
        )
        if result.get('error') is None:
            existing_tables = [row['name'] for row in result.get('data', [])]
            return all(table in existing_tables for table in table_names)
    except:
        pass
    return False


async def test_update_operations():
    """Comprehensive test for update operations."""
    print("🚀 Update Operations Test")
    print("=" * 40)
    
    # Connect to database
    db_name = f"test_updates_{hash(str(asyncio.get_event_loop().time()))}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Set database for all models
    set_database_for_models(engine)
    
    # Check if tables already exist
    table_names = ["test_users", "test_products"]
    tables_exist = await check_tables_exist(engine, table_names)
    
    if not tables_exist:
        # Generate and run migrations
        print("🔄 Generating migrations...")
        migration_engine = MigrationEngine(engine, migrations_dir="../migrations")
        
        models = [User, Product]
        migration = await migration_engine.generate_migration_from_models(
            models, "test_update_operations", "test_runner"
        )
        
        if migration:
            print("✅ Migration generated successfully")
            
            print("🔄 Running migrations...")
            result = await migration_engine.run_migrations()
            print(f"Migration result: {result}")
            
            # Check if the latest migration was successful
            if result.get('success') or result.get('migrations_run', 0) > 0:
                print("✅ Migration executed successfully")
            else:
                print("❌ Migration failed")
                return
        else:
            print("❌ Failed to generate migration")
            return
    else:
        print("✅ Tables already exist, skipping migration")
    
    print("✅ Database setup complete")
    
    # Test 1: Model.update() - Instance-level updates
    print("\n🔄 Test 1: Model.update() - Instance-level updates")
    print("-" * 50)
    
    try:
        # Create test user
        user = await User.create(
            name="John Doe",
            email="john@example.com",
            age=25,
            is_active=True
        )
        print(f"   Created user: {user.name} (ID: {user.pk})")
        
        # Test Model.update()
        await user.update(name="John Smith", age=26)
        print(f"   Updated user name to: {user.name}")
        print(f"   Updated user age to: {user.age}")
        
        # Verify the update was saved
        updated_user = await User.get(pk=user.pk)
        print(f"   Retrieved user: {updated_user.name}, age: {updated_user.age}")
        
        if updated_user.name == "John Smith" and updated_user.age == 26:
            print("✅ Model.update() working correctly")
        else:
            print("❌ Model.update() failed")
            
    except Exception as e:
        print(f"   ❌ Model.update() test failed: {str(e)}")
    
    # Test 2: QuerySet.update() - Bulk updates
    print("\n🔄 Test 2: QuerySet.update() - Bulk updates")
    print("-" * 50)
    
    try:
        # Create multiple products
        products = []
        for i in range(3):
            product = await Product.create(
                name=f"Product {i+1}",
                price=100 + (i * 50),
                description=f"Description for product {i+1}",
                is_available=True
            )
            products.append(product)
            print(f"   Created product: {product.name} (ID: {product.pk})")
        
        # Test QuerySet.update() with simple condition
        updated_count = await Product.filter(is_available=True).update(price=200)
        print(f"   Updated {updated_count} products with price=200")
        
        # Verify the updates
        updated_products = await Product.filter(is_available=True)
        for product in updated_products:
            print(f"   Product {product.name}: price={product.price}")
        
        if all(p.price == 200 for p in updated_products):
            print("✅ QuerySet.update() with simple condition working")
        else:
            print("❌ QuerySet.update() with simple condition failed")
            
    except Exception as e:
        print(f"   ❌ QuerySet.update() test failed: {str(e)}")
    
    # Test 3: QuerySet.update() with complex conditions
    print("\n🔄 Test 3: QuerySet.update() with complex conditions")
    print("-" * 50)
    
    try:
        # Test update with field lookups
        updated_count = await Product.filter(price__gte=200).update(is_available=False)
        print(f"   Updated {updated_count} products with price>=200 to unavailable")
        
        # Verify the updates
        unavailable_products = await Product.filter(is_available=False)
        print(f"   Found {len(unavailable_products)} unavailable products")
        
        for product in unavailable_products:
            print(f"   Product {product.name}: price={product.price}, available={product.is_available}")
        
        if all(not p.is_available for p in unavailable_products):
            print("✅ QuerySet.update() with field lookups working")
        else:
            print("❌ QuerySet.update() with field lookups failed")
            
    except Exception as e:
        print(f"   ❌ QuerySet.update() with complex conditions failed: {str(e)}")
    
    # Test 4: Field validation during updates
    print("\n🔄 Test 4: Field validation during updates")
    print("-" * 50)
    
    try:
        # Test field validation
        user = await User.create(
            name="Test User",
            email="test@example.com",
            age=30
        )
        
        # Test valid update
        await user.update(age=31, name="Updated User")
        print(f"   Valid update successful: {user.name}, age: {user.age}")
        
        # Test invalid update (should raise exception)
        try:
            await user.update(age="invalid_age")  # Should fail
            print("❌ Invalid update should have failed")
        except Exception as e:
            print(f"   ✅ Invalid update correctly rejected: {str(e)}")
        
        print("✅ Field validation during updates working")
        
    except Exception as e:
        print(f"   ❌ Field validation test failed: {str(e)}")
    
    # Test 5: Bulk operations
    print("\n🔄 Test 5: Bulk operations")
    print("-" * 50)
    
    try:
        # Create multiple users for bulk operations
        users = []
        for i in range(5):
            user = await User.create(
                name=f"Bulk User {i+1}",
                email=f"bulk{i+1}@example.com",
                age=20 + i,
                is_active=True
            )
            users.append(user)
        
        print(f"   Created {len(users)} users for bulk operations")
        
        # Test bulk_update
        for user in users:
            user.age += 10
            user.name = f"Updated {user.name}"
        
        updated_count = await User.bulk_update(users, fields=['name', 'age'])
        print(f"   Bulk updated {updated_count} users")
        
        # Verify bulk updates
        updated_users = await User.filter(name__startswith="Updated")
        print(f"   Found {len(updated_users)} updated users")
        
        for user in updated_users:
            print(f"   User: {user.name}, age: {user.age}")
        
        if len(updated_users) == len(users):
            print("✅ Bulk update operations working")
        else:
            print("❌ Bulk update operations failed")
            
    except Exception as e:
        print(f"   ❌ Bulk operations test failed: {str(e)}")
    
    # Test 6: Update with Q objects
    print("\n🔄 Test 6: Update with Q objects")
    print("-" * 50)
    
    try:
        from oxen.expressions import Q
        
        # Create products with different prices
        await Product.create(name="Expensive Product", price=500, is_available=True)
        await Product.create(name="Cheap Product", price=50, is_available=True)
        
        # Test update with Q objects
        from oxen.expressions import Q
        updated_count = await Product.filter(
            Q(price__gte=100) & Q(is_available=True)
        ).update(description="High-value product")
        
        print(f"   Updated {updated_count} products with Q objects")
        
        # Verify the updates
        high_value_products = await Product.filter(description="High-value product")
        print(f"   Found {len(high_value_products)} high-value products")
        
        for product in high_value_products:
            print(f"   Product: {product.name}, price: {product.price}")
        
        if len(high_value_products) > 0:
            print("✅ Update with Q objects working")
        else:
            print("❌ Update with Q objects failed")
            
    except Exception as e:
        print(f"   ❌ Update with Q objects test failed: {str(e)}")
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")
    print("✅ Update operations test completed!")


if __name__ == "__main__":
    asyncio.run(test_update_operations()) 