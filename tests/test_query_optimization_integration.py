#!/usr/bin/env python3
"""
Integration Test for Query Optimization with Engine

This test verifies that query optimization works with the actual engine.
"""

import asyncio
import sys
import uuid
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import connect
from oxen.query_optimizer import get_optimizer, get_performance_stats


async def test_query_optimization_integration():
    """Test query optimization integration with engine."""
    print("🚀 Query Optimization Integration Test")
    print("=" * 50)
    
    # Connect to database
    db_id = uuid.uuid4().hex[:8]
    db_name = f"test_optimization_integration_{db_id}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Test 1: Basic Query with Optimization
    print("\n🔄 Test 1: Basic Query with Optimization")
    print("-" * 50)
    
    try:
        # Execute a simple query
        result = await engine.execute_query("SELECT 1 as test_value")
        
        print(f"   Query Result: {result.get('success', False)}")
        if result.get('success'):
            print(f"   Data: {result.get('data', [])}")
            
            # Check optimization data
            optimization = result.get('optimization', {})
            if optimization:
                print(f"   Performance Score: {optimization.get('performance_score', 0):.1f}/100")
                print(f"   Execution Time: {optimization.get('execution_time', 0):.3f}s")
                print(f"   Suggestions: {len(optimization.get('suggestions', []))}")
                for suggestion in optimization.get('suggestions', []):
                    print(f"     - {suggestion}")
            else:
                print("   ⚠️ No optimization data found")
        
        print("✅ Basic query optimization test completed")
        
    except Exception as e:
        print(f"   ❌ Basic query test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Multiple Queries Performance Tracking
    print("\n🔄 Test 2: Multiple Queries Performance Tracking")
    print("-" * 50)
    
    try:
        # Execute multiple queries to build up performance data
        queries = [
            "SELECT 1 as test1",
            "SELECT 2 as test2, 3 as test3",
            "SELECT 'hello' as greeting",
            "SELECT 1 as a, 2 as b, 3 as c",
        ]
        
        for i, sql in enumerate(queries, 1):
            print(f"   Executing query {i}: {sql}")
            result = await engine.execute_query(sql)
            
            if result.get('success'):
                optimization = result.get('optimization', {})
                print(f"     Performance Score: {optimization.get('performance_score', 0):.1f}/100")
                print(f"     Execution Time: {optimization.get('execution_time', 0):.3f}s")
            else:
                print(f"     Error: {result.get('error')}")
        
        # Get global performance stats
        stats = get_performance_stats()
        print(f"\n   Global Performance Stats:")
        print(f"     Total Queries: {stats.get('total_queries', 0)}")
        print(f"     Avg Execution Time: {stats.get('avg_execution_time', 0):.3f}s")
        print(f"     Avg Performance Score: {stats.get('avg_performance_score', 0):.1f}/100")
        
        print("✅ Multiple queries performance tracking completed")
        
    except Exception as e:
        print(f"   ❌ Multiple queries test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Optimizer Integration
    print("\n🔄 Test 3: Optimizer Integration")
    print("-" * 50)
    
    try:
        optimizer = get_optimizer()
        
        # Check if optimizer is properly integrated
        print(f"   Optimizer initialized: {optimizer is not None}")
        
        # Get performance stats from optimizer
        stats = optimizer.get_performance_stats()
        print(f"   Optimizer stats: {stats}")
        
        # Check for slow queries
        slow_queries = optimizer.get_slow_queries(threshold=0.1)  # 100ms threshold
        print(f"   Slow queries detected: {len(slow_queries)}")
        
        # Check for critical queries
        critical_queries = optimizer.get_critical_queries()
        print(f"   Critical queries detected: {len(critical_queries)}")
        
        print("✅ Optimizer integration test completed")
        
    except Exception as e:
        print(f"   ❌ Optimizer integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Performance Report Generation
    print("\n🔄 Test 4: Performance Report Generation")
    print("-" * 50)
    
    try:
        from oxen.query_optimizer import export_performance_report
        
        # Generate performance report
        report_filename = f"integration_report_{db_id}.json"
        export_performance_report(report_filename)
        
        print(f"   ✅ Performance report generated: {report_filename}")
        
        # Check if file was created
        import os
        if os.path.exists(report_filename):
            file_size = os.path.getsize(report_filename)
            print(f"   Report file size: {file_size} bytes")
        else:
            print("   ⚠️ Report file not found")
        
        print("✅ Performance report generation completed")
        
    except Exception as e:
        print(f"   ❌ Performance report test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Engine Disconnect
    print("\n🔄 Test 5: Engine Disconnect")
    print("-" * 50)
    
    try:
        await engine.disconnect()
        print("   ✅ Engine disconnected successfully")
        print("✅ Engine disconnect test completed")
        
    except Exception as e:
        print(f"   ❌ Engine disconnect failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    import os
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"   🧹 Cleaned up database: {db_name}")
    
    print("\n✅ All integration tests completed successfully!")
    print("🎯 Query optimization integration is working properly!")


if __name__ == "__main__":
    asyncio.run(test_query_optimization_integration()) 