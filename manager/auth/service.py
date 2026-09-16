from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from manager.db.database import SessionLocal
from manager.db.models import User
from manager.auth.passwords import verify_password


class AuthenticationError(Exception):
    pass


def authenticate(
    username: str,
    password: str,
) -> dict[str, object]:
    username = username.strip()

    if not username or not password:
        raise AuthenticationError("Invalid username or password.")

    session = SessionLocal()

    try:
        user = session.scalar(
            select(User).where(
                User.username == username,
            )
        )

        if user is None:
            raise AuthenticationError("Invalid username or password.")

        if not user.is_active:
            raise AuthenticationError("Invalid username or password.")

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise AuthenticationError("Invalid username or password.")

        user.last_login_at = datetime.now(timezone.utc)

        session.commit()

        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
