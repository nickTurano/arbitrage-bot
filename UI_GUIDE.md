# UI Guide

## Overview

The Polymarket-Kalshi Arbitrage Bot includes two professional UI options:

1. **FastAPI Dashboard** - Production-ready REST API and web dashboard
2. **Terminal UI** - Cyberpunk-themed terminal-style interface

## FastAPI Dashboard

### Features

- ✅ Modern, responsive web interface
- ✅ Real-time WebSocket updates
- ✅ REST API endpoints
- ✅ Bot control (start/stop)
- ✅ Live statistics
- ✅ Opportunity tracking
- ✅ Beautiful gradient design

### Usage

```bash
# Run with FastAPI dashboard (default)
arbitrage-bot run

# Or specify explicitly
arbitrage-bot run --ui fastapi

# Custom port
arbitrage-bot run --ui fastapi --port 3000
```

### Access

- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (auto-generated)
- **WebSocket**: ws://localhost:8000/ws

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML |
| `/api/status` | GET | Bot status |
| `/api/stats` | GET | Bot statistics |
| `/api/start` | POST | Start bot |
| `/api/stop` | POST | Stop bot |
| `/api/opportunities` | GET | Recent opportunities |
| `/api/trades` | GET | Recent trades |
| `/ws` | WebSocket | Real-time updates |

### WebSocket Events

**Client receives:**
- `status` - Bot status updates
- `stats` - Statistics updates
- `opportunity` - New opportunity detected
- `trade` - Trade executed
- `error` - Error occurred

## Terminal UI

### Features

- ✅ Cyberpunk-themed terminal design
- ✅ Real-time SocketIO updates
- ✅ Interactive controls
- ✅ Terminal log viewer
- ✅ Opportunity display
- ✅ Statistics dashboard

### Usage

```bash
# Run with terminal UI
arbitrage-bot run --ui terminal

# Custom port
arbitrage-bot run --ui terminal --port 8080
```

### Access

- **Terminal UI**: http://localhost:8080
- **API**: http://localhost:8080/api/status
- **SocketIO**: Auto-connects on page load

### SocketIO Events

**Client emits:**
- `connect` - Connect to server
- `subscribe` - Subscribe to channels
- `start_scan` - Request market scan

**Client receives:**
- `connected` - Connection confirmed
- `status_update` - Status updates
- `opportunity` - New opportunity
- `trade` - Trade executed
- `error` - Error occurred

## Headless Mode

Run without any UI:

```bash
arbitrage-bot run --ui none
```

Perfect for:
- Production deployments
- Automated trading
- Server environments
- Docker containers

## UI Comparison

| Feature | FastAPI Dashboard | Terminal UI |
|---------|-------------------|-------------|
| **Design** | Modern gradient | Cyberpunk terminal |
| **Framework** | FastAPI + WebSocket | Flask + SocketIO |
| **API** | REST + WebSocket | REST + SocketIO |
| **Best For** | Production, monitoring | Demos, interactive |
| **Port** | 8000 (default) | 8080 (default) |

## Customization

### FastAPI Dashboard

Edit `arbitrage_bot/ui/fastapi_dashboard.py`:
- Modify `_get_dashboard_html()` for UI changes
- Add new API endpoints in `_setup_routes()`
- Customize WebSocket events in `_setup_socket_events()`

### Terminal UI

Edit `arbitrage_bot/ui/terminal.py`:
- Modify `_get_terminal_html()` for UI changes
- Add new Flask routes in `_setup_routes()`
- Customize SocketIO events in `_setup_socket_events()`

## Development

### Testing UI Locally

```bash
# Install in dev mode
pip install -e .

# Run FastAPI dashboard
arbitrage-bot run --ui fastapi

# Run Terminal UI
arbitrage-bot run --ui terminal
```

### Adding New Features

1. **New API Endpoint** (FastAPI):
   ```python
   @self.app.get("/api/my-endpoint")
   async def my_endpoint():
       return {"data": "value"}
   ```

2. **New SocketIO Event** (Terminal):
   ```python
   @self.socketio.on("my_event")
   def handle_my_event(data):
       emit("response", {"status": "ok"})
   ```

3. **New WebSocket Message** (FastAPI):
   ```python
   await self._broadcast({
       "type": "my_message",
       "data": {...}
   })
   ```

## Troubleshooting

### Port Already in Use

```bash
# Use different port
arbitrage-bot run --ui fastapi --port 3000
```

### WebSocket Connection Issues

- Check firewall settings
- Verify port is accessible
- Check browser console for errors

### UI Not Loading

- Verify bot is running: `arbitrage-bot run`
- Check logs for errors
- Verify dependencies: `pip install -r requirements.txt`

---

**Both UIs are production-ready and fully functional!** 🚀

