# CLAUDE.md — ftl2-stargate

## What This Is

An authenticated FastAPI gateway for textual-serve backends. Handles Google OAuth login, restricts access by email/domain, and proxies WebSocket connections to textual-serve instances running on localhost. Serves as a single entry point for multiple always-on FTL2 web apps (ai-loop, htop, etc.).

## Architecture

```
Browser → GET /login → Google OAuth → GET /auth/callback (store email in signed session cookie)
        → GET /      → landing page (list apps, user info, logout link)
        → WS /ws/ai-loop → auth check → bidirectional proxy → textual-serve :8001
        → WS /ws/htop    → auth check → bidirectional proxy → textual-serve :8002
```

## Core Components

| File | Purpose |
|------|---------|
| `__init__.py` | CLI entry point — `cli()` parses args and launches uvicorn |
| `app.py` | FastAPI app setup — session middleware (itsdangerous), OAuth registration (authlib), router includes |
| `auth.py` | Auth routes — `/login` (redirect to Google), `/auth/callback` (validate + store session), `/logout` (clear session) |
| `routes.py` | App routes — `GET /` (Jinja2 landing page), `WebSocket /ws/{app_name}` (authenticated proxy) |
| `proxy.py` | WebSocket proxy — `proxy_websocket()` connects to textual-serve backend, relays messages bidirectionally via `asyncio.wait` |
| `config.py` | Environment variable parsing — Google creds, secret key, allowed emails/domain, app:port mappings |
| `templates/index.html` | Jinja2 landing page — dark theme, lists apps with ports, shows user info + logout |

### Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `cli()` | `__init__.py` | Argparse + `uvicorn.run()` |
| `get_current_user(request)` | `auth.py` | Returns email from session or `None` |
| `require_login(request)` | `auth.py` | Returns email or raises `RedirectResponse` to `/login` |
| `proxy_websocket(client_ws, port)` | `proxy.py` | Bidirectional WebSocket relay to `ws://localhost:{port}/ws` |
| `get_apps()` | `config.py` | Parses `APPS` env var into `{name: port}` dict |
| `is_email_allowed(email)` | `config.py` | Checks email against `ALLOWED_EMAILS` and `ALLOWED_DOMAIN` |

## Configuration

All via environment variables (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 client secret |
| `SECRET_KEY` | Signs session cookies (itsdangerous) |
| `ALLOWED_EMAILS` | Comma-separated allowed emails |
| `ALLOWED_DOMAIN` | Allow all `@domain` emails |
| `APPS` | Backend mappings: `name:port,name:port` |

Access control: if both `ALLOWED_EMAILS` and `ALLOWED_DOMAIN` are set, either match grants access. If neither is set, all logins are denied.

## Running

```bash
# Via uvx from GitHub (no install)
uvx --from "git+https://github.com/benthomasson/ftl2-stargate" \
    ftl2-stargate --port 8000

# Local development
pip install -e .
ftl2-stargate --port 8000 --reload
```

## Key Files

```
ftl2_stargate/
├── __init__.py              # CLI entry point
├── app.py                   # FastAPI app, middleware, OAuth setup
├── auth.py                  # Login/callback/logout routes
├── config.py                # Env var parsing and access control
├── proxy.py                 # WebSocket proxy logic
├── routes.py                # Landing page and WebSocket endpoint
└── templates/
    └── index.html           # App launcher page
pyproject.toml               # Hatchling build, Python >=3.13, Apache-2.0
.env.example                 # Required env vars template
```
