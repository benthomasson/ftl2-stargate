from pathlib import Path

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import get_current_user
from .config import get_apps
from .proxy import proxy_websocket

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    email = get_current_user(request)
    if not email:
        return RedirectResponse(url="/login")

    apps = get_apps()
    name = request.session.get("user_name", email)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user_email": email, "user_name": name, "apps": apps},
    )


@router.websocket("/ws/{app_name}")
async def websocket_proxy(websocket: WebSocket, app_name: str):
    email = get_current_user(websocket)
    if not email:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    apps = get_apps()
    if app_name not in apps:
        await websocket.close(code=4404, reason="App not found")
        return

    await websocket.accept()
    try:
        await proxy_websocket(websocket, apps[app_name])
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=1011, reason="Backend connection failed")
