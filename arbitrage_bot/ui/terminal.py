"""
Terminal-Style UI
=================

Beautiful terminal-style web interface with WebSocket support.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import eventlet
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from arbitrage_bot.bot import ArbitrageBot

logger = logging.getLogger(__name__)


class TerminalUI:
    """
    Terminal-style web interface for the arbitrage bot.
    
    Features:
    - Cyberpunk-themed terminal design
    - Real-time WebSocket updates
    - Interactive controls
    - Web3 wallet integration ready
    """
    
    def __init__(
        self,
        bot: ArbitrageBot,
        port: int = 8080,
        host: str = "0.0.0.0",
        debug: bool = False,
    ) -> None:
        """
        Initialize terminal UI.

        Args:
            bot: Arbitrage bot instance
            port: Port to run server on
            host: Host to bind to
            debug: Enable debug mode
        """
        self.bot = bot
        self.port = port
        self.host = host
        self.debug = debug

        # Create Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode="eventlet",
        )

        # Setup routes, socket events, and callbacks
        self._setup_routes()
        self._setup_socket_events()
        self._setup_bot_callbacks()
    
    def _setup_routes(self) -> None:
        """Setup Flask routes."""
        
        @self.app.route("/")
        def index():
            """Serve terminal UI."""
            return render_template_string(get_terminal_html())
        
        @self.app.route("/api/status")
        def get_status():
            """Get bot status."""
            return jsonify(self.bot.get_status())
        
        @self.app.route("/api/stats")
        def get_stats():
            """Get bot statistics."""
            return jsonify(self.bot.get_stats())
        
        @self.app.route("/api/start", methods=["POST"])
        def start_bot():
            """Start the bot."""
            if self.bot._running:
                return jsonify({"error": "Bot is already running"}), 400
            
            eventlet.spawn(self.bot.start)
            return jsonify({"status": "started"})
        
        @self.app.route("/api/stop", methods=["POST"])
        def stop_bot():
            """Stop the bot."""
            if not self.bot._running:
                return jsonify({"error": "Bot is not running"}), 400
            
            eventlet.spawn(self.bot.stop)
            return jsonify({"status": "stopped"})
    
    def _setup_socket_events(self) -> None:
        """Setup SocketIO events."""
        
        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection."""
            logger.info("Client connected")
            emit("connected", {"status": "ok", "timestamp": datetime.utcnow().isoformat()})
            
            # Send initial status
            emit("status_update", {
                "data": self.bot.get_status(),
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info("Client disconnected")
        
        @self.socketio.on("subscribe")
        def handle_subscribe(data):
            """Handle subscription request."""
            logger.info(f"Client subscribed to: {data}")
            emit("subscribed", {"channels": data})
        
        @self.socketio.on("start_scan")
        def handle_start_scan():
            """Handle scan request."""
            logger.info("Scan requested")
            # TODO: Trigger market scan
            emit("scan_started", {"message": "Market scan started"})
    
    def _setup_bot_callbacks(self) -> None:
        """Setup bot callbacks to emit SocketIO events."""
        def on_opportunity(opportunity: Dict[str, Any]) -> None:
            """Emit opportunity to all clients."""
            self.socketio.emit(
                "opportunity",
                {
                    "data": opportunity,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        def on_trade(trade: Dict[str, Any]) -> None:
            """Emit trade to all clients."""
            self.socketio.emit(
                "trade",
                {
                    "data": trade,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        def on_error(error: Exception) -> None:
            """Emit error to all clients."""
            self.socketio.emit(
                "error",
                {
                    "data": {"message": str(error)},
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        self.bot.set_on_opportunity(on_opportunity)
        self.bot.set_on_trade(on_trade)
        self.bot.set_on_error(on_error)
    
    async def run(self) -> None:
        """Run the Flask-SocketIO server."""
        logger.info(f"Starting Terminal UI on http://{self.host}:{self.port}")

        # Start bot in background
        eventlet.spawn(self.bot.start)

        # Run Flask-SocketIO server
        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=self.debug,
            use_reloader=False,
        )
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Polymarket-Kalshi Arbitrage Terminal</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: #0a0e27;
            color: #00ff00;
            overflow-x: hidden;
        }
        
        .terminal {
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .header {
            border: 2px solid #00ff00;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            background: rgba(0, 255, 0, 0.1);
        }
        
        .header h1 {
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
            margin-bottom: 10px;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .status-indicator.connected {
            background: #00ff00;
            box-shadow: 0 0 10px #00ff00;
        }
        
        .status-indicator.disconnected {
            background: #ff0000;
            box-shadow: 0 0 10px #ff0000;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 2fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .panel {
            border: 2px solid #00ff00;
            border-radius: 5px;
            padding: 15px;
            background: rgba(0, 255, 0, 0.05);
            min-height: 400px;
        }
        
        .panel-title {
            color: #00ff00;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 10px;
            margin-bottom: 15px;
            font-weight: bold;
        }
        
        .control-btn {
            background: transparent;
            border: 2px solid #00ff00;
            color: #00ff00;
            padding: 10px 20px;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            margin: 5px;
            transition: all 0.3s;
        }
        
        .control-btn:hover {
            background: rgba(0, 255, 0, 0.2);
            box-shadow: 0 0 15px #00ff00;
        }
        
        .control-btn:active {
            transform: scale(0.95);
        }
        
        .opportunity {
            border: 1px solid #00ff00;
            border-radius: 3px;
            padding: 10px;
            margin-bottom: 10px;
            background: rgba(0, 255, 0, 0.05);
        }
        
        .opportunity-id {
            color: #00ff00;
            font-weight: bold;
        }
        
        .opportunity-profit {
            color: #ffff00;
            font-weight: bold;
        }
        
        .log {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #00ff00;
            background: rgba(0, 0, 0, 0.5);
            padding: 10px;
            border-radius: 3px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
        }
        
        .log-entry.error {
            color: #ff0000;
        }
        
        .log-entry.warning {
            color: #ffff00;
        }
        
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        .stat-item {
            border: 1px solid #00ff00;
            padding: 10px;
            border-radius: 3px;
        }
        
        .stat-label {
            color: #888;
            font-size: 12px;
        }
        
        .stat-value {
            color: #00ff00;
            font-size: 20px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="terminal">
        <div class="header">
            <h1>● ● ●  POLYMARKET-KALSHI ARBITRAGE TERMINAL  ● ● ●</h1>
            <div class="status-bar">
                <div>
                    <span class="status-indicator disconnected" id="statusIndicator"></span>
                    <span id="statusText">Disconnected</span>
                </div>
                <div>
                    <button class="control-btn" onclick="startBot()">▶ START</button>
                    <button class="control-btn" onclick="stopBot()">⏹ STOP</button>
                    <button class="control-btn" onclick="scanMarkets()">🔍 SCAN</button>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="panel">
                <div class="panel-title">CONTROLS & STATS</div>
                <div class="stats" id="stats">
                    <div class="stat-item">
                        <div class="stat-label">Opportunities</div>
                        <div class="stat-value" id="stat-opp">0</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Trades</div>
                        <div class="stat-value" id="stat-trades">0</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Markets</div>
                        <div class="stat-value" id="stat-markets">0</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Uptime</div>
                        <div class="stat-value" id="stat-uptime">0s</div>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">ARBITRAGE OPPORTUNITIES</div>
                <div id="opportunities">
                    <p style="color: #666; text-align: center; padding: 20px;">Waiting for opportunities...</p>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">TERMINAL LOG</div>
                <div class="log" id="log">
                    <div class="log-entry">[SYSTEM] Terminal initialized</div>
                    <div class="log-entry">[SYSTEM] Connecting to server...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        
        socket.on('connect', () => {
            updateStatus(true);
            addLog('Connected to server', 'info');
            socket.emit('subscribe', ['status', 'opportunities', 'trades']);
        });
        
        socket.on('disconnect', () => {
            updateStatus(false);
            addLog('Disconnected from server', 'error');
        });
        
        socket.on('connected', (data) => {
            addLog('Server connection confirmed', 'info');
        });
        
        socket.on('status_update', (data) => {
            updateStats(data.data.stats || {});
        });
        
        socket.on('opportunity', (data) => {
            addOpportunity(data.data);
            addLog(`Opportunity detected: ${data.data.opportunity_id}`, 'info');
        });
        
        socket.on('trade', (data) => {
            addLog(`Trade executed: ${data.data.trade_id}`, 'info');
        });
        
        socket.on('error', (data) => {
            addLog(`Error: ${data.data.message}`, 'error');
        });
        
        function updateStatus(connected) {
            const indicator = document.getElementById('statusIndicator');
            const text = document.getElementById('statusText');
            
            if (connected) {
                indicator.className = 'status-indicator connected';
                text.textContent = 'Connected';
            } else {
                indicator.className = 'status-indicator disconnected';
                text.textContent = 'Disconnected';
            }
        }
        
        function updateStats(stats) {
            document.getElementById('stat-opp').textContent = stats.opportunities_detected || 0;
            document.getElementById('stat-trades').textContent = stats.trades_executed || 0;
            document.getElementById('stat-markets').textContent = stats.markets_scanned || 0;
            
            if (stats.uptime_seconds) {
                const minutes = Math.floor(stats.uptime_seconds / 60);
                const seconds = Math.floor(stats.uptime_seconds % 60);
                document.getElementById('stat-uptime').textContent = `${minutes}m ${seconds}s`;
            }
        }
        
        function addOpportunity(opp) {
            const container = document.getElementById('opportunities');
            if (container.querySelector('p')) {
                container.innerHTML = '';
            }
            
            const div = document.createElement('div');
            div.className = 'opportunity';
            div.innerHTML = `
                <div class="opportunity-id">${opp.opportunity_id || 'N/A'}</div>
                <div>Market: ${opp.market_id || 'N/A'}</div>
                <div class="opportunity-profit">Profit: +${((opp.edge || 0) * 100).toFixed(2)}%</div>
            `;
            
            container.insertBefore(div, container.firstChild);
            
            while (container.children.length > 10) {
                container.removeChild(container.lastChild);
            }
        }
        
        function addLog(message, type = 'info') {
            const log = document.getElementById('log');
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            const timestamp = new Date().toLocaleTimeString();
            entry.textContent = `[${timestamp}] ${message}`;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }
        
        async function startBot() {
            try {
                const response = await fetch('/api/start', { method: 'POST' });
                const data = await response.json();
                addLog('Bot start requested', 'info');
            } catch (error) {
                addLog(`Failed to start bot: ${error.message}`, 'error');
            }
        }
        
        async function stopBot() {
            try {
                const response = await fetch('/api/stop', { method: 'POST' });
                const data = await response.json();
                addLog('Bot stop requested', 'info');
            } catch (error) {
                addLog(`Failed to stop bot: ${error.message}`, 'error');
            }
        }
        
        function scanMarkets() {
            socket.emit('start_scan');
            addLog('Market scan requested', 'info');
        }
        
        // Periodic stats update
        setInterval(async () => {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                updateStats(stats);
            } catch (error) {
                console.error('Failed to fetch stats:', error);
            }
        }, 2000);
    </script>
</body>
</html>
        """
    
    async def run(self) -> None:
        """Run the Flask-SocketIO server."""
        logger.info(f"Starting Terminal UI on http://{self.host}:{self.port}")
        
        # Start bot in background
        eventlet.spawn(self.bot.start)
        
        # Run Flask-SocketIO server
        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=self.debug,
            use_reloader=False,
        )

