# Backend - Ransomware Detection Engine

## Quick Start

From the main project directory, run:
```bash
start.bat
```

Or manually from this directory:
```bash
python main.py
```

## Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Configuration file: `../config/settings.json`

## Directory Structure

- `core/` - File monitoring and decoy management
- `detection/` - Ransomware detection algorithms
- `containment/` - Containment and response actions
- `database/` - Database models and connection
- `api/` - API endpoints (integrated in main.py)
- `data/` - Database files (auto-created)
- `logs/` - Log files (auto-created)

## API Endpoints

- `GET /api/status` - System status
- `GET /api/incidents` - List incidents
- `GET /api/events` - List file events
- `GET /api/alerts` - List alerts
- `GET /api/decoys` - List decoy files
- `GET /api/stats` - Statistics
- `POST /api/containment/{incident_id}` - Trigger containment
- `WebSocket /ws` - Real-time updates

## Running

The server will start on http://localhost:8000
