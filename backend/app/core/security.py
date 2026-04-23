"""
JWT authentication + role-based access control.

Passwords stored with PBKDF2-HMAC-SHA256 (hashlib, no external deps).

Roles:
  admin    — read, create, update, delete
  employee — read, create, update, delete
  auditor  — read only
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

ALGORITHM = "HS256"
PBKDF2_ITERATIONS = 260_000

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

WRITE_ROLES  = {"admin", "employee"}   # create, update
DELETE_ROLES = {"admin"}               # delete only admin
READ_ROLES   = {"admin", "employee", "auditor"}


# ── Password hashing (PBKDF2-HMAC-SHA256) ───────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}:{salt}:{key}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        _, algo, iterations_str, salt, stored_key = hashed.split(":")
        iterations = int(iterations_str)
        check = hashlib.pbkdf2_hmac(
            algo, password.encode(), salt.encode(), iterations
        ).hex()
        return hmac.compare_digest(check, stored_key)
    except Exception:
        return False


# ── In-memory user store ─────────────────────────────────────────────────────

_USERS: dict = {}


def _build_users() -> dict:
    return {
        "admin":    {"role": "admin",    "hashed": hash_password(settings.ADMIN_PASSWORD)},
        "employee": {"role": "employee", "hashed": hash_password(settings.EMPLOYEE_PASSWORD)},
        "auditor":  {"role": "auditor",  "hashed": hash_password(settings.AUDITOR_PASSWORD)},
    }


def get_users() -> dict:
    global _USERS
    if not _USERS:
        _USERS = _build_users()
    return _USERS


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_users().get(username)
    if not user or not verify_password(password, user["hashed"]):
        return None
    return {"username": username, "role": user["role"]}


# ── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": username, "role": role, "exp": expire},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid credentials", "details": []}},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if not username or not role:
            raise _credentials_error()
        return {"username": username, "role": role}
    except JWTError:
        raise _credentials_error()


def require_write(current_user: dict = Depends(get_current_user)) -> dict:
    """Allow admin and employee; deny auditor."""
    if current_user["role"] not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Read-only role cannot perform this action", "details": []}},
        )
    return current_user


def require_delete(current_user: dict = Depends(get_current_user)) -> dict:
    """Allow admin only; employee and auditor cannot delete."""
    if current_user["role"] not in DELETE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Only Admin can delete protocols", "details": []}},
        )
    return current_user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Admin role required", "details": []}},
        )
    return current_user
