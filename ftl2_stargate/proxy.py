import asyncio

from fastapi import WebSocket
import websockets


async def proxy_websocket(client_ws: WebSocket, backend_port: int):
    """Proxy WebSocket messages between the browser and a textual-serve backend."""
    backend_url = f"ws://localhost:{backend_port}/ws"

    async with websockets.connect(backend_url) as backend_ws:
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
