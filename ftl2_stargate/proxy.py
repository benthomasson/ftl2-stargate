import asyncio

from fastapi import WebSocket
import httpx
import websockets


async def proxy_websocket(client_ws: WebSocket, backend: str):
    """Proxy WebSocket messages between the browser and a textual-serve backend."""
    backend_url = f"ws://{backend}/ws"

    async with websockets.connect(backend_url, ping_interval=None, ping_timeout=None) as backend_ws:
        async def client_to_backend():
            try:
                while True:
                    data = await client_ws.receive_text()
                    await backend_ws.send(data)
            except Exception:
                pass

        async def backend_to_client():
            try:
                async for message in backend_ws:
                    if isinstance(message, str):
                        await client_ws.send_text(message)
                    else:
                        await client_ws.send_bytes(message)
            except Exception:
                pass

        # Run both directions concurrently; when either side disconnects, cancel the other
        done, pending = await asyncio.wait(
            [
                asyncio.create_task(client_to_backend()),
                asyncio.create_task(backend_to_client()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()


async def proxy_http(backend: str, path: str, gateway_base: str, app_name: str):
    """Proxy an HTTP request to a textual-serve backend, rewriting URLs."""
    backend_url = f"http://{backend}{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(backend_url)

    content_type = resp.headers.get("content-type", "")
    headers = {}

    if "text/html" in content_type:
        # Rewrite the WebSocket URL to go through our gateway
        body = resp.text
        body = body.replace(
            f"ws://{backend}/ws",
            f"ws://{gateway_base}/app/{app_name}/ws",
        )
        # Rewrite static asset URLs to go through our gateway
        body = body.replace(
            f"http://{backend}/",
            f"http://{gateway_base}/app/{app_name}/",
        )
        # Auto-focus the xterm.js terminal so keystrokes work immediately
        # and intercept the browser back button to send Escape to the terminal
        inject_script = (
            '<script>'
            'document.addEventListener("DOMContentLoaded",()=>{'
            'let t=document.getElementById("terminal");'
            'if(t){new MutationObserver((m,o)=>{'
            'let c=t.querySelector(".xterm-helper-textarea");'
            'if(c){c.focus();o.disconnect()}'
            '}).observe(t,{childList:true,subtree:true})}'
            '});'
            'history.pushState({app:true},"");'
            'window.addEventListener("popstate",()=>{'
            'history.pushState({app:true},"");'
            'let c=document.querySelector(".xterm-helper-textarea");'
            'if(c){'
            'c.focus();'
            'c.dispatchEvent(new KeyboardEvent("keydown",'
            '{key:"Escape",code:"Escape",keyCode:27,bubbles:true}));'
            '}'
            '});'
            '</script>'
        )
        body = body.replace("</head>", inject_script + "</head>")
        return body, resp.status_code, "text/html"

    # For non-HTML (CSS, JS, images), return raw bytes
    for header in ("content-type",):
        if header in resp.headers:
            headers[header] = resp.headers[header]

    return resp.content, resp.status_code, content_type
