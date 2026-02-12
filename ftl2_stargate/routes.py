from pathlib import Path

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from .auth import get_current_user
from .config import get_apps
from .proxy import proxy_websocket, proxy_http

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


@router.get("/app/{app_name}/{path:path}")
async def app_proxy(request: Request, app_name: str, path: str = ""):
    email = get_current_user(request)
    if not email:
        return RedirectResponse(url="/login")

    apps = get_apps()
    if app_name not in apps:
        return Response("App not found", status_code=404)

    backend_path = f"/{path}" if path else "/"
    gateway_base = request.headers.get("host", "localhost:8000")
    body, status_code, content_type = await proxy_http(
        apps[app_name], backend_path, gateway_base, app_name
    )
    return Response(content=body, status_code=status_code, media_type=content_type)


@router.get("/app/{app_name}")
async def app_proxy_root(request: Request, app_name: str):
    return await app_proxy(request, app_name, "")


@router.websocket("/app/{app_name}/ws")
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
