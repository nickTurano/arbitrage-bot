"""
UI Templates
============

HTML templates for both FastAPI and Terminal UIs.
"""


def get_fastapi_dashboard_html(title: str = "Polymarket-Kalshi Arbitrage Bot") -> str:
    """
    Generate FastAPI dashboard HTML.

    Args:
        title: Dashboard title

    Returns:
        HTML string
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
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
            <h1>{title} <span id="status" class="status stopped">Stopped</span></h1>
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
        
        connect();
        
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


def get_terminal_html() -> str:
    """
    Generate terminal-style HTML.

    Returns:
        HTML string
    """
    return """
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

