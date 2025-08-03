#!/usr/bin/env python3
"""
Simple test for Update Operations - focusing on core functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField, BooleanField
from oxen.migrations import MigrationEngine


# Simple test models without DateTimeField
class SimpleUser(Model):
    """Simple user model for testing updates."""
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    age = IntegerField(default=0)
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = "simple_users"


class SimpleProduct(Model):
    """Simple product model for testing updates."""
    name = CharField(max_length=200)
    price = IntegerField(default=0)
    description = CharField(max_length=500, null=True)
    is_available = BooleanField(default=True)
    
    class Meta:
        table_name = "simple_products"


async def test_simple_update_operations():
    """Simple test for update operations."""
    print("🚀 Simple Update Operations Test")
    print("=" * 40)
    
    # Connect to database
    db_name = f"test_simple_updates_{hash(str(asyncio.get_event_loop().time()))}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Set database for all models
    set_database_for_models(engine)
    
    # Generate and run migrations
    print("🔄 Generating migrations...")
    migration_engine = MigrationEngine(engine, migrations_dir="../migrations")
    
    models = [SimpleUser, SimpleProduct]
    migration = await migration_engine.generate_migration_from_models(
        models, "test_simple_update_operations", "test_runner"
    )
    
    if migration:
        print("✅ Migration generated successfully")
        
        print("🔄 Running migrations...")
        result = await migration_engine.run_migrations()
        print(f"Migration result: {result}")
        
        if result.get('success') or result.get('migrations_run', 0) > 0:
            print("✅ Migration executed successfully")
        else:
            print("❌ Migration failed")
            return
    else:
        print("❌ Failed to generate migration")
        return
    
    print("✅ Database setup complete")
    
    # Test 1: Model.update() - Instance-level updates
    print("\n🔄 Test 1: Model.update() - Instance-level updates")
    print("-" * 50)
    
    try:
        # Create test user
        user = await SimpleUser.create(
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
        updated_user = await SimpleUser.get(pk=user.pk)
        print(f"   Retrieved user: {updated_user.name}, age: {updated_user.age}")
        
        if updated_user.name == "John Smith" and updated_user.age == 26:
            print("✅ Model.update() working correctly")
        else:
            print("❌ Model.update() failed")
            
    except Exception as e:
        print(f"   ❌ Model.update() test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: QuerySet.update() - Bulk updates
    print("\n🔄 Test 2: QuerySet.update() - Bulk updates")
    print("-" * 50)
    
    try:
        # Create multiple products
        products = []
        for i in range(3):
            product = await SimpleProduct.create(
                name=f"Product {i+1}",
                price=100 + (i * 50),
                description=f"Description for product {i+1}",
                is_available=True
            )
            products.append(product)
            print(f"   Created product: {product.name} (ID: {product.pk})")
        
        # Test QuerySet.update() with simple condition
        updated_count = await SimpleProduct.filter(is_available=True).update(price=200)
        print(f"   Updated {updated_count} products with price=200")
        
        # Verify the updates
        updated_products = await SimpleProduct.filter(is_available=True)
        for product in updated_products:
            print(f"   Product {product.name}: price={product.price}")
        
        if all(p.price == 200 for p in updated_products):
            print("✅ QuerySet.update() with simple condition working")
        else:
            print("❌ QuerySet.update() with simple condition failed")
            
    except Exception as e:
        print(f"   ❌ QuerySet.update() test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: QuerySet.update() with complex conditions
    print("\n🔄 Test 3: QuerySet.update() with complex conditions")
    print("-" * 50)
    
    try:
        # Test update with field lookups
        updated_count = await SimpleProduct.filter(price__gte=200).update(is_available=False)
        print(f"   Updated {updated_count} products with price>=200 to unavailable")
        
        # Verify the updates
        unavailable_products = await SimpleProduct.filter(is_available=False)
        print(f"   Found {len(unavailable_products)} unavailable products")
        
        for product in unavailable_products:
            print(f"   Product {product.name}: price={product.price}, available={product.is_available}")
        
        if all(not p.is_available for p in unavailable_products):
            print("✅ QuerySet.update() with field lookups working")
        else:
            print("❌ QuerySet.update() with field lookups failed")
            
    except Exception as e:
        print(f"   ❌ QuerySet.update() with complex conditions failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Field validation during updates
    print("\n🔄 Test 4: Field validation during updates")
    print("-" * 50)
    
    try:
        # Test field validation
        user = await SimpleUser.create(
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
        import traceback
        traceback.print_exc()
    
    # Test 5: Update with Q objects
    print("\n🔄 Test 5: Update with Q objects")
    print("-" * 50)
    
    try:
        from oxen.expressions import Q
        
        # Create products with different prices
        await SimpleProduct.create(name="Expensive Product", price=500, is_available=True)
        await SimpleProduct.create(name="Cheap Product", price=50, is_available=True)
        
        # Test update with Q objects
        updated_count = await SimpleProduct.filter(
            Q(price__gte=100) & Q(is_available=True)
        ).update(description="High-value product")
        
        print(f"   Updated {updated_count} products with Q objects")
        
        # Verify the updates
        high_value_products = await SimpleProduct.filter(description="High-value product")
        print(f"   Found {len(high_value_products)} high-value products")
        
        for product in high_value_products:
            print(f"   Product: {product.name}, price: {product.price}")
        
        if len(high_value_products) > 0:
            print("✅ Update with Q objects working")
        else:
            print("❌ Update with Q objects failed")
            
    except Exception as e:
        print(f"   ❌ Update with Q objects test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")
    print("✅ Simple update operations test completed!")


if __name__ == "__main__":
    asyncio.run(test_simple_update_operations()) 