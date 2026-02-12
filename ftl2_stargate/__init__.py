import argparse


def cli():
    parser = argparse.ArgumentParser(description="ftl2-stargate — authenticated gateway for FTL2 web apps")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    import uvicorn

    uvicorn.run("ftl2_stargate.app:app", host=args.host, port=args.port, reload=args.reload)
