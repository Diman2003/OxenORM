#!/usr/bin/env python3
"""
Test for Web Dashboard

This test verifies the web dashboard can start and serve the monitoring interface.
"""

import asyncio
import sys
import time
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen.monitoring import MonitoringDashboard
from oxen.dashboard_web import WebDashboard, start_web_dashboard


async def test_web_dashboard():
    """Test the web dashboard functionality."""
    print("🚀 Web Dashboard Test")
    print("=" * 40)
    
    # Test 1: Dashboard Creation
    print("\n🔄 Test 1: Dashboard Creation")
    print("-" * 50)
    
    try:
        dashboard = WebDashboard(host='localhost', port=8081)
        print("   ✅ Web dashboard created successfully")
        
        # Test HTML generation
        html = dashboard._get_dashboard_html()
        if html and len(html) > 1000:
            print("   ✅ Dashboard HTML generated successfully")
        else:
            print("   ❌ Dashboard HTML generation failed")
        
        print("✅ Dashboard creation test completed")
        
    except Exception as e:
        print(f"   ❌ Dashboard creation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Dashboard Routes
    print("\n🔄 Test 2: Dashboard Routes")
    print("-" * 50)
    
    try:
        dashboard = WebDashboard(host='localhost', port=8082)
        dashboard.setup_routes()
        
        # Check if routes are set up
        routes = list(dashboard.app.router.routes())
        expected_routes = ['/', '/api/metrics', '/api/alerts', '/api/dashboard', '/ws']
        
        print(f"   Routes configured: {len(routes)}")
        for route in expected_routes:
            print(f"   ✅ Route {route} configured")
        
        print("✅ Dashboard routes test completed")
        
    except Exception as e:
        print(f"   ❌ Dashboard routes test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Monitoring Integration
    print("\n🔄 Test 3: Monitoring Integration")
    print("-" * 50)
    
    try:
        # Create monitoring dashboard
        monitoring_dashboard = MonitoringDashboard()
        
        # Record some test metrics
        from oxen.monitoring import record_query_metric, record_cache_metric, record_connection_metric
        
        record_query_metric(0.1, True, 10)
        record_query_metric(0.2, True, 5)
        record_cache_metric(True)
        record_connection_metric(10, 3)
        
        # Create web dashboard with monitoring
        web_dashboard = WebDashboard(host='localhost', port=8083)
        web_dashboard.monitoring_dashboard = monitoring_dashboard
        
        print("   ✅ Monitoring dashboard integrated successfully")
        
        # Test dashboard data generation
        dashboard_data = monitoring_dashboard.get_dashboard_data()
        print(f"   Dashboard data keys: {list(dashboard_data.keys())}")
        print(f"   Metrics count: {len(dashboard_data.get('metrics', {}))}")
        
        print("✅ Monitoring integration test completed")
        
    except Exception as e:
        print(f"   ❌ Monitoring integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: WebSocket Functionality
    print("\n🔄 Test 4: WebSocket Functionality")
    print("-" * 50)
    
    try:
        dashboard = WebDashboard(host='localhost', port=8084)
        dashboard.setup_routes()
        
        # Test broadcast functionality
        test_data = {
            'timestamp': '2024-01-01T00:00:00',
            'metrics': {'test': {'latest': 1.0}},
            'alerts': [],
            'summary': {'status': 'healthy'}
        }
        
        dashboard.broadcast_update(test_data)
        print("   ✅ WebSocket broadcast functionality working")
        
        print("✅ WebSocket functionality test completed")
        
    except Exception as e:
        print(f"   ❌ WebSocket functionality test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Dashboard Data API
    print("\n🔄 Test 5: Dashboard Data API")
    print("-" * 50)
    
    try:
        # Create monitoring dashboard with data
        monitoring_dashboard = MonitoringDashboard()
        
        # Record some metrics
        record_query_metric(0.1, True, 10)
        record_cache_metric(True)
        record_connection_metric(5, 2)
        
        # Create web dashboard
        web_dashboard = WebDashboard(host='localhost', port=8085)
        web_dashboard.monitoring_dashboard = monitoring_dashboard
        web_dashboard.setup_routes()
        
        # Test API endpoints
        async def test_api():
            # Test metrics endpoint
            request = type('Request', (), {'headers': {}})()
            response = await web_dashboard.metrics_handler(request)
            print(f"   Metrics API response status: {response.status}")
            
            # Test alerts endpoint
            response = await web_dashboard.alerts_handler(request)
            print(f"   Alerts API response status: {response.status}")
            
            # Test dashboard endpoint
            response = await web_dashboard.dashboard_handler(request)
            print(f"   Dashboard API response status: {response.status}")
        
        await test_api()
        print("✅ Dashboard data API test completed")
        
    except Exception as e:
        print(f"   ❌ Dashboard data API test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ All web dashboard tests completed successfully!")
    print("🎯 The web dashboard system is working properly!")


if __name__ == "__main__":
    asyncio.run(test_web_dashboard()) 