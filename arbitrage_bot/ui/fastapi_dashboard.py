"""
FastAPI Dashboard
=================

Production-ready FastAPI dashboard with WebSocket support for real-time updates.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from arbitrage_bot.bot import ArbitrageBot
from arbitrage_bot.ui.templates import get_fastapi_dashboard_html

logger = logging.getLogger(__name__)


class FastAPIDashboard:
    """
    FastAPI-based dashboard for the arbitrage bot.
    
    Provides:
    - REST API endpoints for bot control and data
    - WebSocket for real-time updates
    - Embedded HTML dashboard
    """
    
    def __init__(
        self,
        bot: ArbitrageBot,
        port: int = 8000,
        host: str = "0.0.0.0",
        title: str = "Polymarket-Kalshi Arbitrage Bot",
    ) -> None:
        """
        Initialize FastAPI dashboard.

        Args:
            bot: Arbitrage bot instance
            port: Port to run server on
            host: Host to bind to
            title: Dashboard title
        """
        self.bot = bot
        self.port = port
        self.host = host
        self.title = title

        # Create FastAPI app
        self.app = FastAPI(title=title, version="1.0.0")

        # WebSocket connections
        self._active_connections: List[WebSocket] = []

        # Setup routes and callbacks
        self._setup_routes()
        self._setup_bot_callbacks()
    
    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve dashboard HTML."""
            return get_fastapi_dashboard_html(self.title)
        
        @self.app.get("/api/status")
        async def get_status():
            """Get bot status."""
            return self.bot.get_status()
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Get bot statistics."""
            return self.bot.get_stats()
        
        @self.app.post("/api/start")
        async def start_bot():
            """Start the bot."""
            if self.bot._running:
                raise HTTPException(status_code=400, detail="Bot is already running")
            
            asyncio.create_task(self.bot.start())
            return {"status": "started"}
        
        @self.app.post("/api/stop")
        async def stop_bot():
            """Stop the bot."""
            if not self.bot._running:
                raise HTTPException(status_code=400, detail="Bot is not running")
            
            await self.bot.stop()
            return {"status": "stopped"}
        
        @self.app.get("/api/opportunities")
        async def get_opportunities():
            """Get recent opportunities."""
            # TODO: Return actual opportunities from bot
            return {"opportunities": [], "count": 0}
        
        @self.app.get("/api/trades")
        async def get_trades():
            """Get recent trades."""
            # TODO: Return actual trades from bot
            return {"trades": [], "count": 0}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self._active_connections.append(websocket)
            
            try:
                # Send initial status
                await websocket.send_json({
                    "type": "status",
                    "data": self.bot.get_status(),
                })
                
                # Keep connection alive and send updates
                while True:
                    await asyncio.sleep(1.0)
                    
                    # Send periodic updates
                    await websocket.send_json({
                        "type": "stats",
                        "data": self.bot.get_stats(),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
            except WebSocketDisconnect:
                self._active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self._active_connections:
                    self._active_connections.remove(websocket)
    
    def _setup_bot_callbacks(self) -> None:
        """Setup bot callbacks to broadcast updates."""
        async def on_opportunity(opportunity: Dict[str, Any]) -> None:
            """Broadcast opportunity to all connected clients."""
            await self._broadcast(
                {
                    "type": "opportunity",
                    "data": opportunity,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        async def on_trade(trade: Dict[str, Any]) -> None:
            """Broadcast trade to all connected clients."""
            await self._broadcast(
                {
                    "type": "trade",
                    "data": trade,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        def on_error(error: Exception) -> None:
            """Broadcast error to all connected clients."""
            asyncio.create_task(
                self._broadcast(
                    {
                        "type": "error",
                        "data": {"message": str(error)},
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            )

        self.bot.set_on_opportunity(on_opportunity)
        self.bot.set_on_trade(on_trade)
        self.bot.set_on_error(on_error)
    
    async def _broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to all connected WebSocket clients.

        Args:
            message: Message dictionary to broadcast
        """
        disconnected: List[WebSocket] = []

        for connection in self._active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            if conn in self._active_connections:
                self._active_connections.remove(conn)
    
    async def run(self) -> None:
        """Run the FastAPI server."""
        logger.info(f"Starting FastAPI dashboard on http://{self.host}:{self.port}")

        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        server = uvicorn.Server(config)

        # Start bot in background
        asyncio.create_task(self.bot.start())

        await server.serve()
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            margin-left: 10px;
        }}
        
        .status.running {{
            background: #10b981;
            color: white;
        }}
        
        .status.stopped {{
            background: #ef4444;
            color: white;
        }}
        
        .status.dry-run {{
            background: #f59e0b;
            color: white;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .card h2 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        
        .stat {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .stat:last-child {{
            border-bottom: none;
        }}
        
        .stat-label {{
            color: #666;
        }}
        
        .stat-value {{
            font-weight: bold;
            color: #333;
        }}
        
        .stat-value.positive {{
            color: #10b981;
        }}
        
        .stat-value.negative {{
            color: #ef4444;
        }}
        
        .controls {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }}
        
        button {{
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.3s;
        }}
        
        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        
        .btn-start {{
            background: #10b981;
            color: white;
        }}
        
        .btn-stop {{
            background: #ef4444;
            color: white;
        }}
        
        .opportunities {{
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .opportunity {{
            padding: 15px;
            margin-bottom: 10px;
            background: #f9fafb;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        
        .opportunity-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        
        .opportunity-id {{
            font-weight: bold;
            color: #667eea;
        }}
        
        .opportunity-edge {{
            font-weight: bold;
            color: #10b981;
        }}
        
        .connection-status {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }}
        
        .connection-status.connected {{
            background: #10b981;
            color: white;
        }}
        
        .connection-status.disconnected {{
            background: #ef4444;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.title} <span id="status" class="status stopped">Stopped</span></h1>
            <div class="controls">
                <button class="btn-start" onclick="startBot()">Start Bot</button>
                <button class="btn-stop" onclick="stopBot()">Stop Bot</button>
            </div>
        </div>
        
        <div class="connection-status disconnected" id="connectionStatus">Disconnected</div>
        
        <div class="grid">
            <div class="card">
                <h2>Statistics</h2>
                <div id="stats">
                    <div class="stat">
                        <span class="stat-label">Opportunities:</span>
                        <span class="stat-value" id="stat-opportunities">0</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Trades:</span>
                        <span class="stat-value" id="stat-trades">0</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Markets Scanned:</span>
                        <span class="stat-value" id="stat-markets">0</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Uptime:</span>
                        <span class="stat-value" id="stat-uptime">0s</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Recent Opportunities</h2>
                <div class="opportunities" id="opportunities">
                    <p style="color: #999; text-align: center; padding: 20px;">No opportunities yet</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let reconnectTimeout = null;
        
        function connect() {{
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${{protocol}}//${{window.location.host}}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {{
                console.log('WebSocket connected');
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').className = 'connection-status connected';
                if (reconnectTimeout) {{
                    clearTimeout(reconnectTimeout);
                    reconnectTimeout = null;
                }}
            }};
            
            ws.onmessage = (event) => {{
                const message = JSON.parse(event.data);
                handleMessage(message);
            }};
            
            ws.onerror = (error) => {{
                console.error('WebSocket error:', error);
            }};
            
            ws.onclose = () => {{
                console.log('WebSocket disconnected');
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                document.getElementById('connectionStatus').className = 'connection-status disconnected';
                
                // Reconnect after 3 seconds
                if (!reconnectTimeout) {{
                    reconnectTimeout = setTimeout(connect, 3000);
                }}
            }};
        }}
        
        function handleMessage(message) {{
            switch(message.type) {{
                case 'status':
                    updateStatus(message.data);
                    break;
                case 'stats':
                    updateStats(message.data);
                    break;
                case 'opportunity':
                    addOpportunity(message.data);
                    break;
                case 'trade':
                    console.log('Trade executed:', message.data);
                    break;
                case 'error':
                    console.error('Error:', message.data);
                    break;
            }}
        }}
        
        function updateStatus(status) {{
            const statusEl = document.getElementById('status');
            if (status.running) {{
                statusEl.textContent = status.mode === 'dry_run' ? 'Dry Run' : 'Live';
                statusEl.className = 'status ' + (status.mode === 'dry_run' ? 'dry-run' : 'running');
            }} else {{
                statusEl.textContent = 'Stopped';
                statusEl.className = 'status stopped';
            }}
        }}
        
        function updateStats(stats) {{
            document.getElementById('stat-opportunities').textContent = stats.opportunities_detected || 0;
            document.getElementById('stat-trades').textContent = stats.trades_executed || 0;
            document.getElementById('stat-markets').textContent = stats.markets_scanned || 0;
            
            if (stats.uptime_seconds) {{
                const minutes = Math.floor(stats.uptime_seconds / 60);
                const seconds = Math.floor(stats.uptime_seconds % 60);
                document.getElementById('stat-uptime').textContent = `${{minutes}}m ${{seconds}}s`;
            }}
        }}
        
        function addOpportunity(opp) {{
            const container = document.getElementById('opportunities');
            if (container.querySelector('p')) {{
                container.innerHTML = '';
            }}
            
            const div = document.createElement('div');
            div.className = 'opportunity';
            div.innerHTML = `
                <div class="opportunity-header">
                    <span class="opportunity-id">${{opp.opportunity_id || 'N/A'}}</span>
                    <span class="opportunity-edge">+${{(opp.edge * 100).toFixed(2)}}%</span>
                </div>
                <div>Market: ${{opp.market_id || 'N/A'}}</div>
                <div>Type: ${{opp.opportunity_type || 'N/A'}}</div>
            `;
            
            container.insertBefore(div, container.firstChild);
            
            // Keep only last 10
            while (container.children.length > 10) {{
                container.removeChild(container.lastChild);
            }}
        }}
        
        async function startBot() {{
            try {{
                const response = await fetch('/api/start', {{ method: 'POST' }});
                const data = await response.json();
                console.log('Bot started:', data);
            }} catch (error) {{
                console.error('Failed to start bot:', error);
                alert('Failed to start bot: ' + error.message);
            }}
        }}
        
        async function stopBot() {{
            try {{
                const response = await fetch('/api/stop', {{ method: 'POST' }});
                const data = await response.json();
                console.log('Bot stopped:', data);
            }} catch (error) {{
                console.error('Failed to stop bot:', error);
                alert('Failed to stop bot: ' + error.message);
            }}
        }}
        
        // Connect on page load
        connect();
        
        // Refresh stats every 5 seconds
        setInterval(async () => {{
            try {{
                const response = await fetch('/api/stats');
                const stats = await response.json();
                updateStats(stats);
            }} catch (error) {{
                console.error('Failed to fetch stats:', error);
            }}
        }}, 5000);
    </script>
</body>
</html>
        """
    
    async def run(self) -> None:
        """Run the FastAPI server."""
        logger.info(f"Starting FastAPI dashboard on http://{self.host}:{self.port}")
        
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        
        # Start bot in background
        asyncio.create_task(self.bot.start())
        
        await server.serve()

