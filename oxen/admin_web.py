#!/usr/bin/env python3
"""
Web-based Admin Interface for OxenORM

This module provides a web interface for schema visualization,
model management, and database administration.
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

from oxen.admin import AdminInterface, get_admin


class AdminWebInterface:
    """Web-based admin interface for OxenORM."""
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.app = None
        self.runner = None
        self.websockets = []
        self.admin_interface = get_admin()
        
    def setup_routes(self):
        """Setup the web application routes."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for admin interface. Install with: pip install aiohttp")
        
        self.app = web.Application()
        
        # Static files
        self.app.router.add_static('/static', 'static')
        
        # Routes
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/api/schema', self.schema_handler)
        self.app.router.add_get('/api/summary', self.summary_handler)
        self.app.router.add_get('/api/table/{table_name}', self.table_handler)
        self.app.router.add_get('/api/diagram', self.diagram_handler)
        self.app.router.add_get('/api/ddl', self.ddl_handler)
        self.app.router.add_post('/api/export', self.export_handler)
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
        """Serve the main admin page."""
        html = self._get_admin_html()
        return web.Response(text=html, content_type='text/html')
    
    async def schema_handler(self, request):
        """API endpoint for schema data."""
        schema_summary = self.admin_interface.get_schema_summary()
        return web.json_response(schema_summary)
    
    async def summary_handler(self, request):
        """API endpoint for schema summary."""
        summary = self.admin_interface.get_schema_summary()
        return web.json_response(summary)
    
    async def table_handler(self, request):
        """API endpoint for table details."""
        table_name = request.match_info['table_name']
        table_details = self.admin_interface.get_table_details(table_name)
        
        if table_details:
            return web.json_response(table_details)
        else:
            return web.json_response({'error': 'Table not found'}, status=404)
    
    async def diagram_handler(self, request):
        """API endpoint for schema diagram."""
        diagram = self.admin_interface.generate_schema_diagram()
        return web.json_response(diagram)
    
    async def ddl_handler(self, request):
        """API endpoint for SQL DDL statements."""
        ddl_statements = self.admin_interface.generate_sql_ddl()
        return web.json_response(ddl_statements)
    
    async def export_handler(self, request):
        """API endpoint for schema export."""
        try:
            data = await request.json()
            filename = data.get('filename', f'schema_export_{int(time.time())}.json')
            
            self.admin_interface.export_schema_json(filename)
            
            return web.json_response({
                'success': True,
                'filename': filename,
                'message': 'Schema exported successfully'
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
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
                    elif msg.data == 'get_schema':
                        schema_data = self.admin_interface.generate_schema_diagram()
                        await ws.send_str(json.dumps(schema_data))
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
        for ws in self.websockets[:]:
            try:
                asyncio.create_task(ws.send_str(message))
            except Exception as e:
                print(f"Error broadcasting to WebSocket: {e}")
                if ws in self.websockets:
                    self.websockets.remove(ws)
    
    def _get_admin_html(self) -> str:
        """Generate the admin interface HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OxenORM Admin Interface</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
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
        .nav {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .nav-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .nav-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .nav-btn.active {
            background: rgba(255,255,255,0.4);
        }
        .grid {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
            height: calc(100vh - 200px);
        }
        .sidebar {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        .main-content {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .table-item {
            padding: 10px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .table-item:hover {
            background: #e9ecef;
        }
        .table-item.selected {
            background: #007bff;
            color: white;
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
        .column-list {
            margin-top: 15px;
        }
        .column-item {
            padding: 8px;
            margin: 3px 0;
            background: #f8f9fa;
            border-radius: 3px;
            font-size: 0.9em;
        }
        .column-name {
            font-weight: bold;
        }
        .column-type {
            color: #666;
            font-size: 0.8em;
        }
        .diagram-container {
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background: #fafafa;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .export-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 0;
        }
        .export-btn:hover {
            background: #218838;
        }
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 OxenORM Admin Interface</h1>
            <div class="nav">
                <button class="nav-btn active" onclick="showSection('overview')">📊 Overview</button>
                <button class="nav-btn" onclick="showSection('schema')">🏗️ Schema</button>
                <button class="nav-btn" onclick="showSection('diagram')">📈 Diagram</button>
                <button class="nav-btn" onclick="showSection('ddl')">💾 DDL</button>
            </div>
        </div>
        
        <div class="grid">
            <div class="sidebar">
                <h3>📋 Tables</h3>
                <div id="table-list">Loading...</div>
                
                <div id="table-details" style="display: none;">
                    <h4 id="selected-table-name"></h4>
                    <div id="table-metrics"></div>
                    <div id="table-columns"></div>
                </div>
            </div>
            
            <div class="main-content">
                <div id="overview-section">
                    <h2>📊 Schema Overview</h2>
                    <div id="overview-metrics">Loading...</div>
                </div>
                
                <div id="schema-section" style="display: none;">
                    <h2>🏗️ Schema Details</h2>
                    <div id="schema-details">Loading...</div>
                </div>
                
                <div id="diagram-section" style="display: none;">
                    <h2>📈 Schema Diagram</h2>
                    <div class="diagram-container">
                        <div class="loading">Loading diagram...</div>
                    </div>
                </div>
                
                <div id="ddl-section" style="display: none;">
                    <h2>💾 SQL DDL</h2>
                    <button class="export-btn" onclick="exportSchema()">📤 Export Schema</button>
                    <div id="ddl-content">Loading...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentSection = 'overview';
        let selectedTable = null;
        let ws = null;
        
        function connectWebSocket() {
            ws = new WebSocket('ws://' + window.location.host + '/ws');
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateSchemaData(data);
            };
            ws.onclose = function() {
                setTimeout(connectWebSocket, 1000);
            };
        }
        
        function showSection(section) {
            // Hide all sections
            document.getElementById('overview-section').style.display = 'none';
            document.getElementById('schema-section').style.display = 'none';
            document.getElementById('diagram-section').style.display = 'none';
            document.getElementById('ddl-section').style.display = 'none';
            
            // Show selected section
            document.getElementById(section + '-section').style.display = 'block';
            
            // Update nav buttons
            document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            currentSection = section;
            
            // Load section-specific data
            if (section === 'overview') {
                loadOverview();
            } else if (section === 'schema') {
                loadSchema();
            } else if (section === 'diagram') {
                loadDiagram();
            } else if (section === 'ddl') {
                loadDDL();
            }
        }
        
        async function loadOverview() {
            try {
                const response = await fetch('/api/summary');
                const data = await response.json();
                updateOverview(data);
            } catch (error) {
                console.error('Error loading overview:', error);
            }
        }
        
        function updateOverview(data) {
            const container = document.getElementById('overview-metrics');
            
            if (!data.tables_count) {
                container.innerHTML = '<p>No schema data available</p>';
                return;
            }
            
            const html = `
                <div class="card">
                    <h3>📊 Schema Statistics</h3>
                    <div class="metric">
                        <span>Tables</span>
                        <span class="metric-value">${data.tables_count}</span>
                    </div>
                    <div class="metric">
                        <span>Columns</span>
                        <span class="metric-value">${data.columns_count}</span>
                    </div>
                    <div class="metric">
                        <span>Indexes</span>
                        <span class="metric-value">${data.indexes_count}</span>
                    </div>
                    <div class="metric">
                        <span>Constraints</span>
                        <span class="metric-value">${data.constraints_count}</span>
                    </div>
                    <div class="metric">
                        <span>Relationships</span>
                        <span class="metric-value">${data.relationships_count}</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📋 Tables</h3>
                    ${data.tables.map(table => `
                        <div class="metric">
                            <span>${table.name}</span>
                            <span class="metric-value">${table.columns_count} cols</span>
                        </div>
                    `).join('')}
                </div>
            `;
            
            container.innerHTML = html;
        }
        
        async function loadSchema() {
            try {
                const response = await fetch('/api/schema');
                const data = await response.json();
                updateSchema(data);
            } catch (error) {
                console.error('Error loading schema:', error);
            }
        }
        
        function updateSchema(data) {
            const container = document.getElementById('schema-details');
            
            if (!data.tables || data.tables.length === 0) {
                container.innerHTML = '<p>No schema data available</p>';
                return;
            }
            
            const html = data.tables.map(table => `
                <div class="card">
                    <h3>📋 ${table.name}</h3>
                    <div class="metric">
                        <span>Columns</span>
                        <span class="metric-value">${table.columns_count}</span>
                    </div>
                    <div class="metric">
                        <span>Indexes</span>
                        <span class="metric-value">${table.indexes_count}</span>
                    </div>
                    <div class="metric">
                        <span>Constraints</span>
                        <span class="metric-value">${table.constraints_count}</span>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = html;
        }
        
        async function loadDiagram() {
            try {
                const response = await fetch('/api/diagram');
                const data = await response.json();
                updateDiagram(data);
            } catch (error) {
                console.error('Error loading diagram:', error);
            }
        }
        
        function updateDiagram(data) {
            const container = document.querySelector('.diagram-container');
            
            if (!data.nodes || data.nodes.length === 0) {
                container.innerHTML = '<div class="loading">No diagram data available</div>';
                return;
            }
            
            // Simple diagram visualization
            const html = `
                <div style="text-align: center;">
                    <h3>📈 Schema Diagram</h3>
                    <p>${data.nodes.length} tables, ${data.edges.length} relationships</p>
                    <div style="margin-top: 20px;">
                        ${data.nodes.map(node => `
                            <div style="display: inline-block; margin: 10px; padding: 15px; 
                                       background: #e3f2fd; border-radius: 8px; border: 2px solid #2196f3;">
                                <strong>${node.label}</strong><br>
                                <small>${node.data.columns} cols, ${node.data.indexes} idx</small>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            container.innerHTML = html;
        }
        
        async function loadDDL() {
            try {
                const response = await fetch('/api/ddl');
                const data = await response.json();
                updateDDL(data);
            } catch (error) {
                console.error('Error loading DDL:', error);
            }
        }
        
        function updateDDL(data) {
            const container = document.getElementById('ddl-content');
            
            if (!data || Object.keys(data).length === 0) {
                container.innerHTML = '<p>No DDL data available</p>';
                return;
            }
            
            const html = Object.entries(data).map(([tableName, ddl]) => `
                <div class="card">
                    <h3>💾 ${tableName}</h3>
                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">${ddl}</pre>
                </div>
            `).join('');
            
            container.innerHTML = html;
        }
        
        async function exportSchema() {
            try {
                const response = await fetch('/api/export', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        filename: `schema_export_${Date.now()}.json`
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    alert(`Schema exported successfully to ${result.filename}`);
                } else {
                    alert(`Export failed: ${result.error}`);
                }
            } catch (error) {
                console.error('Error exporting schema:', error);
                alert('Export failed');
            }
        }
        
        function updateSchemaData(data) {
            // Update real-time schema data
            if (currentSection === 'overview') {
                updateOverview(data);
            } else if (currentSection === 'diagram') {
                updateDiagram(data);
            }
        }
        
        // Initial load
        loadOverview();
        
        // Connect WebSocket for real-time updates
        connectWebSocket();
    </script>
</body>
</html>
        """
    
    async def start(self):
        """Start the admin web interface."""
        if not AIOHTTP_AVAILABLE:
            print("❌ aiohttp is required for admin interface. Install with: pip install aiohttp")
            return
        
        self.setup_routes()
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        
        print(f"🚀 Admin interface started at http://{self.host}:{self.port}")
        print("🔧 Open your browser to view the admin interface")
    
    async def stop(self):
        """Stop the admin web interface."""
        if self.runner:
            await self.runner.cleanup()
            print("🛑 Admin interface stopped")


def start_admin_interface(host: str = 'localhost', port: int = 8080):
    """Start the admin interface in a separate thread."""
    if not AIOHTTP_AVAILABLE:
        print("❌ aiohttp is required for admin interface. Install with: pip install aiohttp")
        return
    
    async def run_admin():
        admin = AdminWebInterface(host, port)
        await admin.start()
        
        try:
            # Keep the server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await admin.stop()
    
    # Run in a separate thread
    def run_in_thread():
        asyncio.run(run_admin())
    
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    
    return thread 