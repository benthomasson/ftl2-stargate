from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth

from .config import get_secret_key, get_google_client_id, get_google_client_secret
from .auth import router as auth_router
from .routes import router as app_router

app = FastAPI(title="ftl2-stargate")

app.add_middleware(SessionMiddleware, secret_key=get_secret_key())

oauth = OAuth()
oauth.register(
    name="google",
    client_id=get_google_client_id(),
    client_secret=get_google_client_secret(),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

app.include_router(auth_router)
app.include_router(app_router)
