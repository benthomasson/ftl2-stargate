# ftl2-stargate

Authenticated gateway for FTL2 web applications. Handles Google OAuth login and proxies WebSocket connections to [textual-serve](https://github.com/Textualize/textual-serve) backends, providing a single authenticated entry point for multiple always-on apps.

## Architecture

```
                         ┌─────────────────────────────┐
                         │      ftl2-stargate           │
Browser ── HTTPS ──────→ │                             │
                         │  /login   (Google OAuth)     │
                         │  /        (app launcher)     │
                         │  /ws/ai-loop  ─────────────→ │──→ textual-serve :8001
                         │  /ws/htop     ─────────────→ │──→ textual-serve :8002
                         │                             │
                         └─────────────────────────────┘
```

Each textual-serve instance runs on localhost. The gateway handles authentication and WebSocket proxying. Apps run independently — the gateway just connects authenticated users to them.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Google OAuth credentials (GCP Console → APIs & Services → Credentials → OAuth 2.0 Client ID)

## Quick Start

```bash
# Run directly from GitHub — no install needed
uvx --from "git+https://github.com/benthomasson/ftl2-stargate" \
    ftl2-stargate --port 8000

# Or install locally
pip install -e .
ftl2-stargate --port 8000
```

You need to set environment variables before running:

```bash
# Required — Google OAuth
export GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
export GOOGLE_CLIENT_SECRET=your-client-secret

# Required — session cookie signing key
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Required — who can log in (set one or both)
export ALLOWED_EMAILS=ben@example.com
export ALLOWED_DOMAIN=example.com

# Required — app backends (name:port pairs)
export APPS=ai-loop:8001,htop:8002
```

Start textual-serve backends, then the gateway:

```bash
# Start backends
textual serve -c "ftl2-ai-loop --incremental --tui" --port 8001 &
textual serve -c "ftl2-htop -i inventory.yml" --port 8002 &

# Start the gateway
ftl2-stargate --port 8000
```

Open `http://localhost:8000` — you'll be redirected to Google login, then see the app launcher.

## Configuration

All configuration is via environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CLIENT_ID` | Yes | OAuth 2.0 client ID from GCP |
| `GOOGLE_CLIENT_SECRET` | Yes | OAuth 2.0 client secret from GCP |
| `SECRET_KEY` | Yes | Random string for signing session cookies |
| `ALLOWED_EMAILS` | One of these | Comma-separated list of allowed email addresses |
| `ALLOWED_DOMAIN` | One of these | Allow all emails from this domain |
| `APPS` | Yes | App backends as `name:port` pairs (e.g., `ai-loop:8001,htop:8002`) |

See `.env.example` for a template.

## How It Works

1. User visits `/` → redirected to `/login` → redirected to Google OAuth
2. Google calls back to `/auth/callback` with the user's identity
3. Gateway checks the email against `ALLOWED_EMAILS` / `ALLOWED_DOMAIN`
4. If allowed, stores the email in a signed session cookie and redirects to `/`
5. Landing page shows available apps as clickable links
6. Clicking an app opens a WebSocket connection to `/ws/{app_name}`
7. Gateway authenticates the WebSocket, then proxies bidirectionally to the textual-serve backend on localhost

## CLI Options

```
ftl2-stargate [--host HOST] [--port PORT] [--reload]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Port |
| `--reload` | off | Auto-reload for development |
