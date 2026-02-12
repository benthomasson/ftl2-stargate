import os


def get_secret_key() -> str:
    key = os.environ.get("SECRET_KEY", "")
    if not key:
        raise RuntimeError("SECRET_KEY environment variable is required")
    return key


def get_google_client_id() -> str:
    val = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not val:
        raise RuntimeError("GOOGLE_CLIENT_ID environment variable is required")
    return val


def get_google_client_secret() -> str:
    val = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not val:
        raise RuntimeError("GOOGLE_CLIENT_SECRET environment variable is required")
    return val


def get_allowed_emails() -> set[str]:
    val = os.environ.get("ALLOWED_EMAILS", "")
    if not val:
        return set()
    return {e.strip().lower() for e in val.split(",") if e.strip()}


def get_allowed_domain() -> str:
    return os.environ.get("ALLOWED_DOMAIN", "").strip().lower()


def get_apps() -> dict[str, int]:
    """Parse APPS env var into {name: port} mapping.

    Format: name:port,name:port (e.g. "ai-loop:8001,htop:8002")
    """
    val = os.environ.get("APPS", "")
    if not val:
        return {}
    apps = {}
    for entry in val.split(","):
        entry = entry.strip()
        if not entry:
            continue
        name, _, port = entry.partition(":")
        if not name or not port:
            raise ValueError(f"Invalid APPS entry: {entry!r} (expected name:port)")
        apps[name.strip()] = int(port.strip())
    return apps


def is_email_allowed(email: str) -> bool:
    email = email.strip().lower()
    allowed_emails = get_allowed_emails()
    allowed_domain = get_allowed_domain()

    if allowed_emails and email in allowed_emails:
        return True
    if allowed_domain and email.endswith(f"@{allowed_domain}"):
        return True
    # If neither is configured, deny all
    if not allowed_emails and not allowed_domain:
        return False
    return False
