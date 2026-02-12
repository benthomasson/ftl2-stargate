from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from .config import is_email_allowed

router = APIRouter()


def get_current_user(request: Request) -> str | None:
    """Return the authenticated user's email, or None."""
    return request.session.get("user_email")


def require_login(request: Request) -> str:
    """Return the authenticated user's email, or redirect to /login.

    Use this in route handlers — raises RedirectResponse if unauthenticated.
    """
    email = get_current_user(request)
    if not email:
        raise RedirectResponse(url="/login", status_code=302)
    return email


@router.get("/login")
async def login(request: Request):
    from .app import oauth

    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, str(redirect_uri))


@router.get("/auth/callback")
async def auth_callback(request: Request):
    from .app import oauth

    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo", {})
    email = userinfo.get("email", "")

    if not email or not is_email_allowed(email):
        return RedirectResponse(url="/login?error=unauthorized")

    request.session["user_email"] = email
    request.session["user_name"] = userinfo.get("name", email)
    return RedirectResponse(url="/")


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")
