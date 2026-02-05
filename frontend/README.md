# TFT Bot Dashboard

React frontend for monitoring TFT game state and coach recommendations in real-time.

## Quick Start

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

## Pages

- **Home** (`/`) - Landing page
- **Dashboard** (`/dashboard`) - Live game state monitoring
- **Logs** (`/logs`) - Decision history and coach recommendations

## Features

- Real-time WebSocket connection to API
- Live gold/HP/level tracking
- Coach decision streaming
- Decision history with persistence (localStorage)

## API Connection

Connects to the backend API at `http://127.0.0.1:8000`:

- `GET /state` - Current game state
- `WS /ws/state` - Stream game state
- `WS /ws/decisions` - Stream coach decisions

Make sure `run_state_api.py` is running before starting the frontend.

## Stack

- React 18
- Vite
- React Router
- WebSocket hooks
