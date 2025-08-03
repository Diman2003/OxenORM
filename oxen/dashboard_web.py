#!/usr/bin/env python3
"""
Web-based Dashboard for OxenORM Monitoring

This module provides a simple web interface for viewing monitoring metrics.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
import threading

try:
    from aiohttp import web, WSMsgType
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class WebDashboard:
    """Web-based dashboard for monitoring metrics."""
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.app = None
        self.runner = None
        self.websockets = []
        self.monitoring_dashboard = None
        
    def setup_routes(self):
        """Setup the web application routes."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for web dashboard. Install with: pip install aiohttp")
        
        self.app = web.Application()
        
        # Static files
        self.app.router.add_static('/static', 'static')
        
        # Routes
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/api/metrics', self.metrics_handler)
        self.app.router.add_get('/api/alerts', self.alerts_handler)
        self.app.router.add_get('/api/dashboard', self.dashboard_handler)
        self.app.router.add_get('/ws', self.websocket_handler)
        
        # Middleware for CORS
        self.app.middlewares.append(self.cors_middleware)
    
    async def cors_middleware(self, request, handler):
        """CORS middleware for cross-origin requests."""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    async def index_handler(self, request):
        """Serve the main dashboard page."""
        html = self._get_dashboard_html()
        return web.Response(text=html, content_type='text/html')
    
    async def metrics_handler(self, request):
        """API endpoint for metrics data."""
        if not self.monitoring_dashboard:
            return web.json_response({'error': 'Monitoring dashboard not initialized'})
        
        metrics = self.monitoring_dashboard.monitor.collector.metrics
        return web.json_response(metrics)
    
    async def alerts_handler(self, request):
        """API endpoint for alerts data."""
        if not self.monitoring_dashboard:
            return web.json_response({'error': 'Monitoring dashboard not initialized'})
        
        alerts = self.monitoring_dashboard.monitor.alert_manager.get_active_alerts()
        alert_data = [
            {
                'id': alert.id,
                'level': alert.level.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'metric_name': alert.metric_name,
                'current_value': alert.current_value,
                'threshold': alert.threshold
            }
            for alert in alerts
        ]
        return web.json_response(alert_data)
    
    async def dashboard_handler(self, request):
        """API endpoint for complete dashboard data."""
        if not self.monitoring_dashboard:
            return web.json_response({'error': 'Monitoring dashboard not initialized'})
        
        dashboard_data = self.monitoring_dashboard.get_dashboard_data()
        return web.json_response(dashboard_data)
    
    async def websocket_handler(self, request):
        """WebSocket handler for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.append(ws)
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    if msg.data == 'ping':
                        await ws.send_str('pong')
                elif msg.type == WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        finally:
            if ws in self.websockets:
                self.websockets.remove(ws)
        
        return ws
    
    def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast updates to all connected WebSocket clients."""
        if not self.websockets:
            return
        
        message = json.dumps(data)
        for ws in self.websockets[:]:  # Copy list to avoid modification during iteration
            try:
                asyncio.create_task(ws.send_str(message))
            except Exception as e:
                print(f"Error broadcasting to WebSocket: {e}")
                if ws in self.websockets:
                    self.websockets.remove(ws)
    
    def _get_dashboard_html(self) -> str:
        """Generate the dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OxenORM Monitoring Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }
        .status.healthy { background-color: #4caf50; }
        .status.warning { background-color: #ff9800; }
        .status.critical { background-color: #f44336; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: #333;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .metric-value {
            font-weight: bold;
            color: #2196f3;
        }
        .alert {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .alert.warning {
            background-color: #fff3cd;
            border-color: #ffc107;
            color: #856404;
        }
        .alert.critical {
            background-color: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }
        .chart-container {
            height: 200px;
            margin-top: 10px;
        }
        .refresh-btn {
            background: #2196f3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background: #1976d2;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 OxenORM Monitoring Dashboard</h1>
            <div class="status" id="system-status">Loading...</div>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
        
        <div class="grid">
            <div class="card">
                <h3>📊 Performance Metrics</h3>
                <div id="performance-metrics">Loading...</div>
            </div>
            
            <div class="card">
                <h3>🚨 Active Alerts</h3>
                <div id="alerts">Loading...</div>
            </div>
            
            <div class="card">
                <h3>📈 System Health</h3>
                <div id="system-health">Loading...</div>
            </div>
            
            <div class="card">
                <h3>🔗 Connection Pool</h3>
                <div id="connection-pool">Loading...</div>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        
        function connectWebSocket() {
            ws = new WebSocket('ws://' + window.location.host + '/ws');
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            ws.onclose = function() {
                setTimeout(connectWebSocket, 1000);
            };
        }
        
        function updateDashboard(data) {
            // Update system status
            const status = document.getElementById('system-status');
            status.textContent = data.summary?.status || 'Unknown';
            status.className = 'status ' + (data.summary?.status || 'unknown');
            
            // Update performance metrics
            updatePerformanceMetrics(data.metrics);
            
            // Update alerts
            updateAlerts(data.alerts);
            
            // Update system health
            updateSystemHealth(data.summary);
            
            // Update connection pool
            updateConnectionPool(data.metrics);
        }
        
        function updatePerformanceMetrics(metrics) {
            const container = document.getElementById('performance-metrics');
            if (!metrics) {
                container.innerHTML = '<p>No metrics available</p>';
                return;
            }
            
            let html = '';
            for (const [name, stats] of Object.entries(metrics)) {
                if (stats.latest !== undefined) {
                    html += `
                        <div class="metric">
                            <span>${name}</span>
                            <span class="metric-value">${stats.latest.toFixed(3)}</span>
                        </div>
                    `;
                }
            }
            container.innerHTML = html || '<p>No metrics available</p>';
        }
        
        function updateAlerts(alerts) {
            const container = document.getElementById('alerts');
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<p>✅ No active alerts</p>';
                return;
            }
            
            let html = '';
            alerts.forEach(alert => {
                html += `
                    <div class="alert ${alert.level}">
                        <strong>${alert.level.toUpperCase()}:</strong> ${alert.message}
                    </div>
                `;
            });
            container.innerHTML = html;
        }
        
        function updateSystemHealth(summary) {
            const container = document.getElementById('system-health');
            if (!summary) {
                container.innerHTML = '<p>No system health data</p>';
                return;
            }
            
            const html = `
                <div class="metric">
                    <span>Status</span>
                    <span class="metric-value">${summary.status}</span>
                </div>
                <div class="metric">
                    <span>Active Alerts</span>
                    <span class="metric-value">${summary.active_alerts}</span>
                </div>
                <div class="metric">
                    <span>Total Metrics</span>
                    <span class="metric-value">${summary.total_metrics}</span>
                </div>
            `;
            container.innerHTML = html;
        }
        
        function updateConnectionPool(metrics) {
            const container = document.getElementById('connection-pool');
            if (!metrics || !metrics.connection_pool_usage) {
                container.innerHTML = '<p>No connection pool data</p>';
                return;
            }
            
            const usage = metrics.connection_pool_usage.latest || 0;
            const active = metrics.active_connections?.latest || 0;
            
            const html = `
                <div class="metric">
                    <span>Pool Usage</span>
                    <span class="metric-value">${(usage * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Active Connections</span>
                    <span class="metric-value">${active}</span>
                </div>
            `;
            container.innerHTML = html;
        }
        
        async function refreshData() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        // Initial load
        refreshData();
        
        // Connect WebSocket for real-time updates
        connectWebSocket();
        
        // Auto-refresh every 5 seconds
        setInterval(refreshData, 5000);
    </script>
</body>
</html>
        """
    
    async def start(self, monitoring_dashboard=None):
        """Start the web dashboard."""
        if not AIOHTTP_AVAILABLE:
            print("❌ aiohttp is required for web dashboard. Install with: pip install aiohttp")
            return
        
        self.monitoring_dashboard = monitoring_dashboard
        self.setup_routes()
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        
        print(f"🚀 Web dashboard started at http://{self.host}:{self.port}")
        print("📊 Open your browser to view the monitoring dashboard")
    
    async def stop(self):
        """Stop the web dashboard."""
        if self.runner:
            await self.runner.cleanup()
            print("🛑 Web dashboard stopped")


def start_web_dashboard(host: str = 'localhost', port: int = 8080, monitoring_dashboard=None):
    """Start the web dashboard in a separate thread."""
    if not AIOHTTP_AVAILABLE:
        print("❌ aiohttp is required for web dashboard. Install with: pip install aiohttp")
        return
    
    async def run_dashboard():
        dashboard = WebDashboard(host, port)
        await dashboard.start(monitoring_dashboard)
        
        try:
            # Keep the server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await dashboard.stop()
    
    # Run in a separate thread
    def run_in_thread():
        asyncio.run(run_dashboard())
    
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    
    return thread 