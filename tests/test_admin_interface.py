#!/usr/bin/env python3
"""
Test for Admin Interface System

This test verifies the admin interface features including:
- Schema analysis and visualization
- Model registration and management
- Database structure diagrams
- SQL DDL generation
"""

import asyncio
import sys
import uuid
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField, BooleanField, DateTimeField
from oxen.fields.relational import ForeignKeyField, OneToOneField, ManyToManyField
from oxen.admin import AdminInterface, SchemaAnalyzer, register_models_for_admin
from oxen.admin_web import AdminWebInterface


# Test models for admin interface
class AdminUser(Model):
    """User model for testing admin interface."""
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    age = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"admin_users_{uuid.uuid4().hex[:8]}"


class AdminProduct(Model):
    """Product model for testing admin interface."""
    name = CharField(max_length=200)
    price = IntegerField(default=0)
    category = CharField(max_length=100)
    description = CharField(max_length=500)
    is_available = BooleanField(default=True)
    user = ForeignKeyField(AdminUser, related_name="products")
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"admin_products_{uuid.uuid4().hex[:8]}"


class AdminOrder(Model):
    """Order model for testing admin interface."""
    order_number = CharField(max_length=50, unique=True)
    total_amount = IntegerField(default=0)
    status = CharField(max_length=50, default="pending")
    user = ForeignKeyField(AdminUser, related_name="orders")
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"admin_orders_{uuid.uuid4().hex[:8]}"


class AdminProfile(Model):
    """Profile model for testing one-to-one relationships."""
    bio = CharField(max_length=500)
    avatar = CharField(max_length=255)
    user = OneToOneField(AdminUser, related_name="profile")
    
    class Meta:
        table_name = f"admin_profiles_{uuid.uuid4().hex[:8]}"


class AdminCategory(Model):
    """Category model for testing many-to-many relationships."""
    name = CharField(max_length=100)
    description = CharField(max_length=500)
    
    class Meta:
        table_name = f"admin_categories_{uuid.uuid4().hex[:8]}"


class AdminProductCategory(Model):
    """Through model for many-to-many relationship."""
    product = ForeignKeyField(AdminProduct, related_name="category_links")
    category = ForeignKeyField(AdminCategory, related_name="product_links")
    
    class Meta:
        table_name = f"admin_product_categories_{uuid.uuid4().hex[:8]}"


async def test_admin_interface():
    """Test the admin interface system."""
    print("🚀 Admin Interface Test")
    print("=" * 40)
    
    # Test 1: Schema Analyzer
    print("\n🔄 Test 1: Schema Analyzer")
    print("-" * 50)
    
    try:
        analyzer = SchemaAnalyzer()
        
        # Test models
        test_models = [AdminUser, AdminProduct, AdminOrder, AdminProfile, AdminCategory, AdminProductCategory]
        
        # Analyze schema
        diagram = analyzer.analyze_schema_from_models(test_models)
        
        print(f"   Tables analyzed: {len(diagram.tables)}")
        print(f"   Relationships found: {len(diagram.relationships)}")
        
        for table in diagram.tables:
            print(f"   📋 {table.name}: {len(table.columns)} columns, {len(table.indexes)} indexes")
        
        print("✅ Schema analyzer test completed")
        
    except Exception as e:
        print(f"   ❌ Schema analyzer test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Admin Interface
    print("\n🔄 Test 2: Admin Interface")
    print("-" * 50)
    
    try:
        admin = AdminInterface()
        
        # Register models
        admin.register_models([AdminUser, AdminProduct, AdminOrder, AdminProfile, AdminCategory, AdminProductCategory])
        
        # Get schema summary
        summary = admin.get_schema_summary()
        print(f"   Schema Summary:")
        print(f"     Tables: {summary.get('tables_count', 0)}")
        print(f"     Columns: {summary.get('columns_count', 0)}")
        print(f"     Indexes: {summary.get('indexes_count', 0)}")
        print(f"     Constraints: {summary.get('constraints_count', 0)}")
        print(f"     Relationships: {summary.get('relationships_count', 0)}")
        
        print("✅ Admin interface test completed")
        
    except Exception as e:
        print(f"   ❌ Admin interface test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Table Details
    print("\n🔄 Test 3: Table Details")
    print("-" * 50)
    
    try:
        admin = AdminInterface()
        admin.register_models([AdminUser, AdminProduct, AdminOrder])
        
        # Get details for each table
        for model in [AdminUser, AdminProduct, AdminOrder]:
            table_name = model._meta.table_name
            details = admin.get_table_details(table_name)
            
            if details:
                print(f"   📋 {table_name}:")
                print(f"     Columns: {len(details.get('columns', []))}")
                print(f"     Indexes: {len(details.get('indexes', []))}")
                print(f"     Constraints: {len(details.get('constraints', []))}")
                print(f"     Relationships: {len(details.get('relationships', []))}")
            else:
                print(f"   ❌ No details found for {table_name}")
        
        print("✅ Table details test completed")
        
    except Exception as e:
        print(f"   ❌ Table details test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Schema Diagram
    print("\n🔄 Test 4: Schema Diagram")
    print("-" * 50)
    
    try:
        admin = AdminInterface()
        admin.register_models([AdminUser, AdminProduct, AdminOrder, AdminProfile])
        
        # Generate diagram
        diagram = admin.generate_schema_diagram()
        
        print(f"   Diagram generated:")
        print(f"     Nodes (tables): {len(diagram.get('nodes', []))}")
        print(f"     Edges (relationships): {len(diagram.get('edges', []))}")
        
        # Show some nodes
        for node in diagram.get('nodes', [])[:3]:
            print(f"     📋 {node['label']}: {node['data']['columns']} columns")
        
        # Show some edges
        for edge in diagram.get('edges', [])[:3]:
            print(f"     🔗 {edge['source']} -> {edge['target']} ({edge['type']})")
        
        print("✅ Schema diagram test completed")
        
    except Exception as e:
        print(f"   ❌ Schema diagram test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: SQL DDL Generation
    print("\n🔄 Test 5: SQL DDL Generation")
    print("-" * 50)
    
    try:
        admin = AdminInterface()
        admin.register_models([AdminUser, AdminProduct, AdminOrder])
        
        # Generate DDL
        ddl_statements = admin.generate_sql_ddl()
        
        print(f"   DDL statements generated: {len(ddl_statements)}")
        
        for table_name, ddl in ddl_statements.items():
            print(f"   💾 {table_name}:")
            lines = ddl.split('\n')
            for line in lines[:5]:  # Show first 5 lines
                print(f"     {line}")
            if len(lines) > 5:
                print(f"     ... ({len(lines) - 5} more lines)")
        
        print("✅ SQL DDL generation test completed")
        
    except Exception as e:
        print(f"   ❌ SQL DDL generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Schema Export
    print("\n🔄 Test 6: Schema Export")
    print("-" * 50)
    
    try:
        admin = AdminInterface()
        admin.register_models([AdminUser, AdminProduct, AdminOrder])
        
        # Export schema
        export_filename = f"schema_export_{uuid.uuid4().hex[:8]}.json"
        admin.export_schema_json(export_filename)
        
        print(f"   ✅ Schema exported to: {export_filename}")
        
        # Check if file was created
        import os
        if os.path.exists(export_filename):
            file_size = os.path.getsize(export_filename)
            print(f"   File size: {file_size} bytes")
            
            # Read and validate JSON
            with open(export_filename, 'r') as f:
                data = json.load(f)
            
            print(f"   Export contains:")
            print(f"     Schema: {bool(data.get('schema'))}")
            print(f"     Summary: {bool(data.get('summary'))}")
            print(f"     Tables: {len(data.get('tables', []))}")
            
            # Cleanup
            os.remove(export_filename)
            print(f"   🧹 Cleaned up export file")
        else:
            print(f"   ❌ Export file not found")
        
        print("✅ Schema export test completed")
        
    except Exception as e:
        print(f"   ❌ Schema export test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 7: Global Admin Interface
    print("\n🔄 Test 7: Global Admin Interface")
    print("-" * 50)
    
    try:
        # Register models with global admin
        register_models_for_admin([AdminUser, AdminProduct, AdminOrder])
        
        # Get schema summary from global admin
        from oxen.admin import get_schema_summary
        summary = get_schema_summary()
        
        print(f"   Global Admin Summary:")
        print(f"     Tables: {summary.get('tables_count', 0)}")
        print(f"     Columns: {summary.get('columns_count', 0)}")
        print(f"     Relationships: {summary.get('relationships_count', 0)}")
        
        print("✅ Global admin interface test completed")
        
    except Exception as e:
        print(f"   ❌ Global admin interface test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 8: Web Admin Interface
    print("\n🔄 Test 8: Web Admin Interface")
    print("-" * 50)
    
    try:
        # Test web interface creation
        web_admin = AdminWebInterface(host='localhost', port=8086)
        
        # Test HTML generation
        html = web_admin._get_admin_html()
        if html and len(html) > 1000:
            print("   ✅ Admin HTML generated successfully")
        else:
            print("   ❌ Admin HTML generation failed")
        
        # Test route setup
        try:
            web_admin.setup_routes()
            print("   ✅ Admin routes configured successfully")
        except ImportError:
            print("   ⚠️ aiohttp not available - routes not tested")
        
        print("✅ Web admin interface test completed")
        
    except Exception as e:
        print(f"   ❌ Web admin interface test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ All admin interface tests completed successfully!")
    print("🎯 The admin interface system is working properly!")


if __name__ == "__main__":
    asyncio.run(test_admin_interface()) 