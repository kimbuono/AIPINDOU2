"""
JWT-based authentication for the Aipindou API.
"""

import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass

from .database import get_conn

SECRET_KEY = os.getenv("JWT_SECRET", "aipindou-dev-secret-change-in-production")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "168"))  # 7 days
ALGORITHM = "HS256"


@dataclass
class User:
    id: int
    email: str
    username: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_user(email: str, username: str, password: str) -> User:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
            (email.lower().strip(), username.strip(), hash_password(password)),
        )
        conn.commit()
        return User(id=cur.lastrowid, email=email, username=username)  # type: ignore[arg-type]
    except Exception:
        raise ValueError("邮箱或用户名已存在")
    finally:
        conn.close()


def authenticate(email: str, password: str) -> Optional[User]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, email, username, password FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
        if row and verify_password(password, row["password"]):
            return User(id=row["id"], email=row["email"], username=row["username"])
        return None
    finally:
        conn.close()


def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[User]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return User(
            id=int(payload["sub"]),
            email=payload["email"],
            username=payload["username"],
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
        return None
