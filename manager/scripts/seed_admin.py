from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import select

from manager.auth.passwords import hash_password
from manager.db.database import SessionLocal
from manager.db.models import User


def main() -> None:
    username = os.getenv(
        "ADMIN_USERNAME",
        "admin",
    ).strip()

    password = os.getenv("ADMIN_PASSWORD")

    if not username:
        raise SystemExit("ADMIN_USERNAME cannot be empty.")

    if not password:
        raise SystemExit("ADMIN_PASSWORD must be set.")

    now = datetime.now(timezone.utc)

    session = SessionLocal()

    try:
        user = session.scalar(
            select(User).where(
                User.username == username,
            )
        )

        if user is None:
            user = User(
                username=username,
                password_hash=hash_password(password),
                role="ADMIN",
                is_active=True,
                created_at=now,
                updated_at=now,
            )

            session.add(user)

            print(f"Admin user '{username}' created.")

        else:
            user.password_hash = hash_password(password)
            user.role = "ADMIN"
            user.is_active = True
            user.updated_at = now

            print(f"Admin user '{username}' updated.")

        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
