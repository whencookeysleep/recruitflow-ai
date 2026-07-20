import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings
from app.schemas import LoginRequest, LoginOut


@dataclass(frozen=True)
class CurrentUser:
    username: str
    role: str
    display_name: str


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _sign(message: str, secret: str) -> str:
    return _b64encode(hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest())


def authenticate(request: LoginRequest, settings: Settings) -> LoginOut:
    accounts = {
        settings.demo_hr_username: (settings.demo_hr_password, "hr", "HR Demo"),
        settings.demo_department_username: (
            settings.demo_department_password,
            "department",
            "Department Demo",
        ),
    }
    account = accounts.get(request.username)
    if account is None or not hmac.compare_digest(request.password, account[0]):
        raise ValueError("Invalid username or password")
    display_name = request.display_name.strip() if request.display_name else account[2]

    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.auth_token_hours)
    payload = {
        "username": request.username,
        "role": account[1],
        "display_name": display_name,
        "exp": int(expires_at.timestamp()),
    }
    encoded = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    token = f"{encoded}.{_sign(encoded, settings.auth_secret)}"
    return LoginOut(access_token=token, role=account[1], display_name=display_name)


def current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        encoded, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(encoded, settings.auth_secret)):
            raise ValueError("invalid signature")
        payload = json.loads(_b64decode(encoded))
        if int(payload["exp"]) <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("expired token")
        if payload["role"] not in {"hr", "department"}:
            raise ValueError("invalid role")
        return CurrentUser(
            username=str(payload["username"]),
            role=str(payload["role"]),
            display_name=str(payload["display_name"]),
        )
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def require_role(*roles: str):
    def dependency(user: CurrentUser = Depends(current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role {user.role} is not allowed")
        return user

    return dependency
