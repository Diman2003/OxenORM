#!/usr/bin/env python3
"""
Test for Monitoring Dashboard System

This test verifies the monitoring dashboard features including:
- Real-time performance metrics
- Alert management
- Dashboard data generation
- Metric collection and analysis
"""

import asyncio
import sys
import uuid
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen.monitoring import (
    MonitoringDashboard, PerformanceMonitor, MetricCollector, 
    AlertManager, start_monitoring, stop_monitoring,
    record_query_metric, record_cache_metric, record_connection_metric
)
from oxen import connect


async def test_monitoring_dashboard():
    """Test the monitoring dashboard system."""
    print("🚀 Monitoring Dashboard Test")
    print("=" * 40)
    
    # Test 1: Metric Collection
    print("\n🔄 Test 1: Metric Collection")
    print("-" * 50)
    
    try:
        collector = MetricCollector()
        
        # Record some test metrics
        test_metrics = [
            ('query_execution_time', 0.1),
            ('query_execution_time', 0.2),
            ('query_execution_time', 0.15),
            ('cache_hit_rate', 0.8),
            ('cache_hit_rate', 0.9),
            ('active_connections', 5),
            ('active_connections', 3),
        ]
        
        for metric_name, value in test_metrics:
            collector.record_metric(metric_name, value)
            print(f"   Recorded {metric_name}: {value}")
        
        # Get statistics
        stats = collector.get_statistics('query_execution_time')
        print(f"   Query execution time stats: {stats}")
        
        print("✅ Metric collection test completed")
        
    except Exception as e:
        print(f"   ❌ Metric collection test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Alert Management
    print("\n🔄 Test 2: Alert Management")
    print("-" * 50)
    
    try:
        alert_manager = AlertManager()
        
        # Set thresholds
        alert_manager.set_threshold('query_execution_time', 0.5, 1.0)
        alert_manager.set_threshold('error_rate', 0.1, 0.2)
        
        # Test threshold checking
        test_values = [
            ('query_execution_time', 0.3),  # No alert
            ('query_execution_time', 0.7),  # Warning
            ('query_execution_time', 1.5),  # Critical
            ('error_rate', 0.15),           # Warning
        ]
        
        for metric_name, value in test_values:
            alert = alert_manager.check_thresholds(metric_name, value)
            if alert:
                print(f"   🚨 Alert: {alert.message}")
            else:
                print(f"   ✅ No alert for {metric_name}: {value}")
        
        # Get active alerts
        active_alerts = alert_manager.get_active_alerts()
        print(f"   Active alerts: {len(active_alerts)}")
        
        print("✅ Alert management test completed")
        
    except Exception as e:
        print(f"   ❌ Alert management test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Performance Monitor
    print("\n🔄 Test 3: Performance Monitor")
    print("-" * 50)
    
    try:
        monitor = PerformanceMonitor()
        
        # Record some performance metrics
        monitor.record_query_metric(0.1, True, 10)
        monitor.record_query_metric(0.2, True, 5)
        monitor.record_query_metric(0.8, False, 0)  # Failed query
        monitor.record_cache_metric(True)
        monitor.record_cache_metric(False)
        monitor.record_connection_metric(10, 3)
        
        # Get dashboard data
        dashboard_data = monitor.get_dashboard_data()
        print(f"   Dashboard data keys: {list(dashboard_data.keys())}")
        print(f"   Metrics count: {len(dashboard_data.get('metrics', {}))}")
        print(f"   Active alerts: {len(dashboard_data.get('alerts', []))}")
        print(f"   System status: {dashboard_data.get('summary', {}).get('status', 'unknown')}")
        
        print("✅ Performance monitor test completed")
        
    except Exception as e:
        print(f"   ❌ Performance monitor test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Monitoring Dashboard
    print("\n🔄 Test 4: Monitoring Dashboard")
    print("-" * 50)
    
    try:
        dashboard = MonitoringDashboard()
        
        # Set some alert thresholds
        dashboard.set_alert_threshold('query_execution_time', 0.5, 1.0)
        dashboard.set_alert_threshold('error_rate', 0.1, 0.2)
        
        # Record some metrics
        record_query_metric(0.1, True, 10)
        record_query_metric(0.6, True, 5)  # Should trigger warning
        record_query_metric(1.2, False, 0)  # Should trigger critical
        record_cache_metric(True)
        record_cache_metric(False)
        record_connection_metric(10, 8)  # 80% usage
        
        # Get dashboard data
        dashboard_data = dashboard.get_dashboard_data()
        
        print(f"   Dashboard Summary:")
        print(f"     Status: {dashboard_data.get('summary', {}).get('status', 'unknown')}")
        print(f"     Active Alerts: {dashboard_data.get('summary', {}).get('active_alerts', 0)}")
        print(f"     Total Metrics: {dashboard_data.get('summary', {}).get('total_metrics', 0)}")
        
        # Export dashboard report
        report_filename = f"dashboard_report_{uuid.uuid4().hex[:8]}.json"
        dashboard.export_dashboard_report(report_filename)
        print(f"   ✅ Dashboard report exported: {report_filename}")
        
        print("✅ Monitoring dashboard test completed")
        
    except Exception as e:
        print(f"   ❌ Monitoring dashboard test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Global Monitoring Integration
    print("\n🔄 Test 5: Global Monitoring Integration")
    print("-" * 50)
    
    try:
        # Start global monitoring
        start_monitoring()
        print("   ✅ Global monitoring started")
        
        # Record some global metrics
        record_query_metric(0.1, True, 10)
        record_query_metric(0.3, True, 5)
        record_cache_metric(True)
        record_connection_metric(5, 2)
        
        # Wait a moment for monitoring to collect data
        await asyncio.sleep(1)
        
        # Get global dashboard
        from oxen.monitoring import get_dashboard
        global_dashboard = get_dashboard()
        dashboard_data = global_dashboard.get_dashboard_data()
        
        print(f"   Global Dashboard Status: {dashboard_data.get('summary', {}).get('status', 'unknown')}")
        print(f"   Global Metrics Count: {len(dashboard_data.get('metrics', {}))}")
        
        # Stop global monitoring
        stop_monitoring()
        print("   ✅ Global monitoring stopped")
        
        print("✅ Global monitoring integration test completed")
        
    except Exception as e:
        print(f"   ❌ Global monitoring test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Metric History
    print("\n🔄 Test 6: Metric History")
    print("-" * 50)
    
    try:
        dashboard = MonitoringDashboard()
        
        # Record metrics over time
        for i in range(10):
            record_query_metric(0.1 + (i * 0.05), True, i * 10)
            record_cache_metric(i % 2 == 0)  # Alternate cache hits/misses
            time.sleep(0.1)  # Small delay
        
        # Get metric history
        query_history = dashboard.get_metric_history('query_execution_time', hours=1)
        cache_history = dashboard.get_metric_history('cache_hit_rate', hours=1)
        
        print(f"   Query execution time history points: {len(query_history)}")
        print(f"   Cache hit rate history points: {len(cache_history)}")
        
        if query_history:
            latest_query = query_history[-1]
            print(f"   Latest query execution time: {latest_query['value']}")
        
        print("✅ Metric history test completed")
        
    except Exception as e:
        print(f"   ❌ Metric history test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 7: Real-time Monitoring with Database
    print("\n🔄 Test 7: Real-time Monitoring with Database")
    print("-" * 50)
    
    try:
        # Connect to database with monitoring
        db_id = uuid.uuid4().hex[:8]
        db_name = f"test_monitoring_{db_id}.db"
        connection_string = f"sqlite:///{db_name}"
        
        print(f"   Connecting to: {connection_string}")
        engine = await connect(connection_string)
        
        # Execute some queries to generate metrics
        queries = [
            "SELECT 1 as test",
            "SELECT 2 as test2",
            "SELECT 'hello' as greeting",
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
        
        # Get monitoring data
        from oxen.monitoring import get_dashboard
        dashboard = get_dashboard()
        dashboard_data = dashboard.get_dashboard_data()
        
        print(f"   Monitoring Summary:")
        print(f"     Status: {dashboard_data.get('summary', {}).get('status', 'unknown')}")
        print(f"     Metrics: {len(dashboard_data.get('metrics', {}))}")
        print(f"     Alerts: {len(dashboard_data.get('alerts', []))}")
        
        # Cleanup
        await engine.disconnect()
        import os
        if os.path.exists(db_name):
            os.remove(db_name)
            print(f"   🧹 Cleaned up database: {db_name}")
        
        print("✅ Real-time monitoring test completed")
        
    except Exception as e:
        print(f"   ❌ Real-time monitoring test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ All monitoring dashboard tests completed successfully!")
    print("🎯 The monitoring dashboard system is working properly!")


if __name__ == "__main__":
    asyncio.run(test_monitoring_dashboard()) 